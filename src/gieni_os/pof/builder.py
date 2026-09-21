"""
Gieni OS Probate Opportunity File (POF v2.0) Builder
Constructs the canonical 8-profile product deliverable.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class PropertyProfile:
    apn: str
    situs_address: str
    city_state_zip: str
    legal_description: str
    avm_market_estimate: float
    total_assessed_value: float
    land_value: float
    improvement_value: float
    landuse: str
    pas_score: float

@dataclass
class OwnershipProfile:
    legal_title_vesting: str
    ownership_complexity_score: int
    net_distributable_equity: float
    net_equity_pct: float
    target_wholesale_mao: float
    senior_mortgage_balance: float
    municipal_liens: float
    estimated_repairs: float
    is_free_and_clear: bool

@dataclass
class ControlProfile:
    control_archetype: str
    primary_decision_maker: str
    relationship_to_decedent: str
    heir_count: int
    occupancy: str

@dataclass
class AuthorityProfile:
    authority_tier: str
    court_oversight_model: str
    can_execute_psa: bool
    court_confirmation_required: bool
    statutory_basis: str
    statutory_power_scope: str

@dataclass
class OpportunityProfile:
    composite_viability_score: int
    priority_tier: str
    deal_friction_score: int
    dispatch_sla: str

@dataclass
class RiskProfile:
    overall_deal_risk_classification: str
    foreclosure_acceleration_risk: bool

@dataclass
class EvidencePackage:
    qc_certification_stamp: str
    recorded_deed_instrument: str
    source_dockets: List[str] = field(default_factory=list)

@dataclass
class RecommendedAction:
    transaction_strategy: str
    first_touch_channel: str
    conversational_framing_script: str

@dataclass
class ProbateOpportunityFile:
    opportunity_id: str
    docket_number: str
    estate_name: str
    property_profile: PropertyProfile
    ownership_profile: OwnershipProfile
    control_profile: ControlProfile
    authority_profile: AuthorityProfile
    opportunity_profile: OpportunityProfile
    risk_profile: RiskProfile
    evidence_package: EvidencePackage
    recommended_action: RecommendedAction

class ProbateOpportunityFileBuilder:
    @staticmethod
    def build(
        opp_id: str,
        pia: Dict[str, Any],
        pra: Dict[str, Any],
        oia: Dict[str, Any],
        cia: Dict[str, Any],
        ara: Dict[str, Any],
        osa: Dict[str, Any],
        qca: Dict[str, Any],
        raw_filing: Dict[str, Any]
    ) -> ProbateOpportunityFile:
        # 1. Property Profile
        city_state = pra.get("city_state")
        zipcode = pra.get("zipcode")
        city_state_zip = f"{city_state} {zipcode}".strip() if (city_state or zipcode) else None
        avm = oia.get("net_equity_waterfall", {}).get("estimated_arv") or pra.get("avm_market_estimate", 0.0)
        total_assessed = pra.get("total_assessed_value", 0.0)
        prop_profile = PropertyProfile(
            apn=pra.get("apn"),
            situs_address=pra.get("situs_address"),
            city_state_zip=city_state_zip,
            legal_description=pra.get("legal_description"),
            avm_market_estimate=float(avm) if avm is not None else 0.0,
            total_assessed_value=float(total_assessed) if total_assessed is not None else 0.0,
            land_value=float(pra.get("land_value", 0.0)),
            improvement_value=float(pra.get("improvement_value", 0.0)),
            landuse=pra.get("landuse"),
            pas_score=float(pra.get("pas_score", 0.0))
        )

        # 2. Ownership Profile
        waterfall = oia.get("net_equity_waterfall", {})
        net_equity = waterfall.get("net_distributable_equity")
        net_equity_val = float(net_equity) if net_equity is not None else 0.0
        arv = float(waterfall.get("estimated_arv", avm or 1.0))
        target_mao = waterfall.get("target_mao")
        target_mao_val = float(target_mao) if target_mao is not None else 0.0
        own_profile = OwnershipProfile(
            legal_title_vesting=oia.get("vesting_classification"),
            ownership_complexity_score=int(oia.get("ownership_complexity_score", 0)),
            net_distributable_equity=net_equity_val,
            net_equity_pct=round(net_equity_val / max(1.0, arv), 3) if arv > 0 else 0.0,
            target_wholesale_mao=target_mao_val,
            senior_mortgage_balance=float(waterfall.get("senior_mortgage_balance", 0.0)),
            municipal_liens=float(waterfall.get("municipal_liens", 0.0)),
            estimated_repairs=float(waterfall.get("estimated_repairs", 0.0)),
            is_free_and_clear=bool(waterfall.get("is_free_and_clear", False))
        )

        # 3. Control Profile
        dm_dossier = cia.get("decision_maker_dossier", {})
        ctrl_profile = ControlProfile(
            control_archetype=cia.get("control_archetype"),
            primary_decision_maker=dm_dossier.get("name"),
            relationship_to_decedent=dm_dossier.get("relationship"),
            heir_count=int(dm_dossier.get("heir_count", 0)),
            occupancy=dm_dossier.get("occupancy")
        )

        # 4. Authority Profile
        auth_profile = AuthorityProfile(
            authority_tier=ara.get("authority_tier"),
            court_oversight_model=ara.get("court_oversight_model"),
            can_execute_psa=bool(ara.get("can_execute_psa", False)),
            court_confirmation_required=bool(ara.get("court_confirmation_required", False)),
            statutory_basis=ara.get("statutory_basis"),
            statutory_power_scope=ara.get("legal_summary")
        )

        # 5. Opportunity Profile
        opp_profile = OpportunityProfile(
            composite_viability_score=int(osa.get("composite_score", 0)),
            priority_tier=osa.get("priority_band", "Unassigned"),
            deal_friction_score=int(osa.get("deal_friction_score", 0)),
            dispatch_sla=osa.get("sla_assignment", "Standard")
        )

        # 6. Risk Profile
        dfs_score = int(osa.get("deal_friction_score", 0))
        computed_risk = "Low Risk" if dfs_score <= 5 else ("High Risk" if dfs_score > 15 else "Moderate Risk")
        risk_profile = RiskProfile(
            overall_deal_risk_classification=osa.get("risk_classification", computed_risk),
            foreclosure_acceleration_risk=bool(oia.get("foreclosure_risk", False))
        )

        # 7. Evidence Package
        recorded_deed = (
            qca.get("recorded_deed_instrument")
            or pra.get("recorded_deed_instrument")
            or oia.get("recorded_deed_instrument")
        )
        ev_package = EvidencePackage(
            qc_certification_stamp=qca.get("qc_certification", "Pending QC"),
            recorded_deed_instrument=recorded_deed,
            source_dockets=[raw_filing.get("case_number")] if raw_filing.get("case_number") else []
        )

        # 8. Recommended Action
        rec_action = RecommendedAction(
            transaction_strategy=osa.get("recommended_strategy", "Pending Evaluation"),
            first_touch_channel=cia.get("first_touch_channel"),
            conversational_framing_script=cia.get("recommended_outreach_strategy")
        )

        return ProbateOpportunityFile(
            opportunity_id=opp_id,
            docket_number=raw_filing.get("case_number", "26-4-01892-3"),
            estate_name=raw_filing.get("decedent_name", "Estate of Harold M. Albright"),
            property_profile=prop_profile,
            ownership_profile=own_profile,
            control_profile=ctrl_profile,
            authority_profile=auth_profile,
            opportunity_profile=opp_profile,
            risk_profile=risk_profile,
            evidence_package=ev_package,
            recommended_action=rec_action
        )
