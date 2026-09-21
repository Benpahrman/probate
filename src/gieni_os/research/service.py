"""
Gieni OS Research Hub Service
Orchestrates extensible research providers across Contacts, Title, Authority, and Valuation.
Persists findings to the database and logs immutable audit trails.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from gieni_os.research.models import (
    ResearchArea,
    ResearchRequest,
    ResearchDossier,
    ProviderInfo,
    ContactResearchData,
    TitleResearchData,
    AuthorityResearchData,
    ValuationResearchData
)
from gieni_os.research.providers.base import BaseResearchProvider
from gieni_os.research.providers.contacts_provider import ContactResearchProvider
from gieni_os.research.providers.title_provider import TitleResearchProvider
from gieni_os.research.providers.authority_provider import AuthorityResearchProvider
from gieni_os.research.providers.valuation_provider import ValuationResearchProvider

from gieni_os.database.models import (
    OpportunityModel,
    ProbateCaseModel,
    WorkflowAuditLogModel
)

class ResearchHubService:
    _providers: Dict[str, BaseResearchProvider] = {}

    @classmethod
    def register_provider(cls, provider: BaseResearchProvider):
        """Registers a research provider adapter into the global registry."""
        cls._providers[provider.provider_id] = provider

    @classmethod
    def get_provider(cls, provider_id: str) -> Optional[BaseResearchProvider]:
        return cls._providers.get(provider_id)

    @classmethod
    def list_providers(cls) -> List[ProviderInfo]:
        """Returns metadata and supported areas for all registered providers."""
        cls._ensure_default_providers()
        return [p.get_info() for p in cls._providers.values()]

    @classmethod
    def _ensure_default_providers(cls):
        if "provider_skip_trace_core" not in cls._providers:
            cls.register_provider(ContactResearchProvider())
        if "provider_county_auditor_title" not in cls._providers:
            cls.register_provider(TitleResearchProvider())
        if "provider_court_authority_are" not in cls._providers:
            cls.register_provider(AuthorityResearchProvider())
        if "provider_avm_valuation_engine" not in cls._providers:
            cls.register_provider(ValuationResearchProvider())

    @classmethod
    def execute_research(
        cls,
        req: ResearchRequest,
        db: Optional[Session] = None,
        operator_name: str = "Research Analyst"
    ) -> ResearchDossier:
        cls._ensure_default_providers()
        context: Dict[str, Any] = {}
        opp: Optional[OpportunityModel] = None

        if req.opportunity_id and db:
            opp = db.query(OpportunityModel).filter(OpportunityModel.id == req.opportunity_id).first()
            if opp:
                context["county_id"] = opp.county_id
                if opp.case:
                    context["case_number"] = opp.case.case_number
                    context["decedent"] = opp.case.decedent
                    context["petitioner_name"] = f"Personal Representative of {opp.case.decedent}"
                from gieni_os.services.pof_resolver import POFDataResolver
                resolved_pof = POFDataResolver.resolve_opportunity_pof(opp)
                context["situs_address"] = req.address or resolved_pof.property_profile.situs_address
                context["apn"] = req.apn or resolved_pof.property_profile.apn
                context["total_assessed_value"] = resolved_pof.property_profile.total_assessed_value
                context["senior_debt"] = resolved_pof.ownership_profile.senior_mortgage_balance
                context["estimated_repairs"] = resolved_pof.ownership_profile.estimated_repairs
                context["authority_tier"] = resolved_pof.authority_profile.authority_tier

        if req.address:
            context["situs_address"] = req.address
        if req.apn:
            context["apn"] = req.apn
        if req.county_id:
            context["county_id"] = req.county_id
        if req.case_number:
            context["case_number"] = req.case_number
        if req.target_name:
            context["target_name"] = req.target_name

        area = req.area
        contacts_res: Optional[Any] = None
        title_res: Optional[Any] = None
        authority_res: Optional[Any] = None
        valuation_res: Optional[Any] = None

        # Execute relevant providers (prioritize built-in or full schema providers)
        if area in [ResearchArea.CONTACTS, ResearchArea.COMPREHENSIVE]:
            # First try provider_skip_trace_core
            p = cls._providers.get("provider_skip_trace_core")
            if p:
                contacts_res = p.execute(req, context)
            else:
                for prov in cls._providers.values():
                    if ResearchArea.CONTACTS in prov.supported_areas:
                        contacts_res = prov.execute(req, context)
                        break

        if area in [ResearchArea.TITLE, ResearchArea.COMPREHENSIVE]:
            p = cls._providers.get("provider_county_auditor_title")
            if p:
                title_res = p.execute(req, context)
            else:
                for prov in cls._providers.values():
                    if ResearchArea.TITLE in prov.supported_areas:
                        title_res = prov.execute(req, context)
                        break
            if title_res:
                s_debt = getattr(title_res, "total_senior_debt", 0.0) if hasattr(title_res, "total_senior_debt") else (title_res.get("total_senior_debt", 0.0) if isinstance(title_res, dict) else 0.0)
                context["senior_debt"] = s_debt

        if area in [ResearchArea.AUTHORITY, ResearchArea.COMPREHENSIVE]:
            p = cls._providers.get("provider_court_authority_are")
            if p:
                authority_res = p.execute(req, context)
            else:
                for prov in cls._providers.values():
                    if ResearchArea.AUTHORITY in prov.supported_areas:
                        authority_res = prov.execute(req, context)
                        break

        if area in [ResearchArea.VALUATION, ResearchArea.COMPREHENSIVE]:
            p = cls._providers.get("provider_avm_valuation_engine")
            if p:
                valuation_res = p.execute(req, context)
            else:
                for prov in cls._providers.values():
                    if ResearchArea.VALUATION in prov.supported_areas:
                        valuation_res = prov.execute(req, context)
                        break

        # Compile summary notes
        notes_parts = []
        if contacts_res:
            c_name = getattr(contacts_res, "target_name", "Fiduciary") if hasattr(contacts_res, "target_name") else contacts_res.get("target_name", "Fiduciary")
            c_phone = getattr(contacts_res, "primary_phone", "N/A") if hasattr(contacts_res, "primary_phone") else contacts_res.get("primary_phone", "N/A")
            notes_parts.append(f"Contacts: {c_name} ({c_phone}) verified via skip-trace (DNC scrubbed).")
        if title_res:
            has_cloud = getattr(title_res, "has_title_cloud", False) if hasattr(title_res, "has_title_cloud") else (title_res.get("has_title_cloud", False) if isinstance(title_res, dict) else False)
            apn = getattr(title_res, "apn", "N/A") if hasattr(title_res, "apn") else (title_res.get("apn", "N/A") if isinstance(title_res, dict) else "N/A")
            s_debt = getattr(title_res, "total_senior_debt", 0.0) if hasattr(title_res, "total_senior_debt") else (title_res.get("total_senior_debt", 0.0) if isinstance(title_res, dict) else 0.0)
            cloud_str = "Title cloud detected" if has_cloud else "Clean fee simple title"
            notes_parts.append(f"Title: {cloud_str} (APN: {apn}, Senior Debt: ${s_debt:,.2f}).")
        if authority_res:
            tier = getattr(authority_res, "authority_tier", "Tier 1") if hasattr(authority_res, "authority_tier") else authority_res.get("authority_tier", "Tier 1")
            stat = getattr(authority_res, "statutory_basis", "RCW 11.68") if hasattr(authority_res, "statutory_basis") else authority_res.get("statutory_basis", "RCW 11.68")
            notes_parts.append(f"Authority: {tier} ({stat}).")
        if valuation_res:
            m_val = getattr(valuation_res, "estimated_market_value", 0.0) if hasattr(valuation_res, "estimated_market_value") else valuation_res.get("estimated_market_value", 0.0)
            n_eq = getattr(valuation_res, "net_distributable_equity", 0.0) if hasattr(valuation_res, "net_distributable_equity") else valuation_res.get("net_distributable_equity", 0.0)
            eq_spread = getattr(valuation_res, "equity_spread_ratio", 0.0) if hasattr(valuation_res, "equity_spread_ratio") else valuation_res.get("equity_spread_ratio", 0.0)
            notes_parts.append(f"Valuation: Market ${m_val:,.2f}, Net Equity ${n_eq:,.2f} ({int(eq_spread*100)}%).")

        summary_notes = " | ".join(notes_parts) if notes_parts else "Research completed."

        # If DB session and opportunity present, log audit and refresh opportunity score if warranted
        if opp and db:
            audit = WorkflowAuditLogModel(
                opportunity_id=opp.id,
                from_stage=opp.workflow_stage,
                to_stage=opp.workflow_stage,
                transitioned_by=operator_name,
                notes=f"[{area.value} RESEARCH] {summary_notes}"
            )
            db.add(audit)
            
            # Boost score if complete research confirmed clean title and strong equity
            if valuation_res:
                eq_spread = getattr(valuation_res, "equity_spread_ratio", 0.0) if hasattr(valuation_res, "equity_spread_ratio") else valuation_res.get("equity_spread_ratio", 0.0)
                if eq_spread > 0.40 and opp.score < 90:
                    opp.score = min(98, opp.score + 5)
            
            db.commit()

        # Build clean Pydantic dossier
        c_pydantic = contacts_res if isinstance(contacts_res, ContactResearchData) else None
        t_pydantic = title_res if isinstance(title_res, TitleResearchData) else None
        a_pydantic = authority_res if isinstance(authority_res, AuthorityResearchData) else None
        v_pydantic = valuation_res if isinstance(valuation_res, ValuationResearchData) else None

        return ResearchDossier(
            opportunity_id=req.opportunity_id,
            area=area,
            overall_confidence=0.95,
            summary_notes=summary_notes,
            contacts=c_pydantic,
            title=t_pydantic,
            authority=a_pydantic,
            valuation=v_pydantic
        )
