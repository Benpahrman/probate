"""
Unit and Integration Tests for Gieni OS Research Hub & Extensible Providers
Validates:
- ContactResearchProvider, TitleResearchProvider, AuthorityResearchProvider, ValuationResearchProvider
- Provider extendability: custom provider registration
- ResearchHubService 360-degree deep sweeps and DB persistence
- REST API endpoints:
  - GET  /api/research/providers
  - POST /api/research/execute
  - POST /api/research/contacts
  - POST /api/research/title
  - GET  /api/research/{opportunity_id}/dossier
  - GET  /api/opportunities/{opportunity_id}/workbench with contact_summary
"""

import pytest
from fastapi.testclient import TestClient
from gieni_os.api.main import app
from gieni_os.database.connection import SessionLocal
from gieni_os.database.models import OpportunityModel, ProbateCaseModel
from gieni_os.research.models import (
    ResearchArea,
    ResearchRequest,
    ResearchDossier,
    ProviderInfo
)
from gieni_os.research.providers.base import BaseResearchProvider
from gieni_os.research.providers.contacts_provider import ContactResearchProvider
from gieni_os.research.providers.title_provider import TitleResearchProvider
from gieni_os.research.providers.authority_provider import AuthorityResearchProvider
from gieni_os.research.providers.valuation_provider import ValuationResearchProvider
from gieni_os.research.service import ResearchHubService

client = TestClient(app)

def test_contacts_research_provider():
    provider = ContactResearchProvider()
    assert provider.provider_id == "provider_skip_trace_core"
    assert ResearchArea.CONTACTS in provider.supported_areas
    
    # 1. When authentic phones are provided in docket / context
    req = ResearchRequest(
        target_name="Eleanor Vance",
        area=ResearchArea.CONTACTS,
        county_id="cty_pierce"
    )
    result = provider.execute(req, context={
        "decedent": "Harold Vance",
        "petitioner_relationship": "Surviving Spouse",
        "raw_phones": ["+12534440182", "+12534440199"],
        "relatives": [{"name": "Eleanor Vance Jr.", "relationship": "Daughter"}]
    })
    
    assert result.target_name == "Eleanor Vance"
    assert len(result.phones) == 2
    assert any(p.line_type == "WIRELESS" for p in result.phones)
    assert result.primary_phone == "+12534440182"
    assert result.dnc_scrubbed is True
    assert len(result.relatives_and_heirs) > 0
    assert result.recommended_outreach_channel == "PHONE_CALL"
    assert "condolences" in (result.outreach_script_template or "").lower()

    # 2. Authentic Empty / Pending State when no phones exist
    empty_result = provider.execute(req, context={"decedent": "Harold Vance"})
    assert empty_result.primary_phone is None
    assert len(empty_result.phones) == 0
    assert empty_result.skip_trace_confidence == 0.0
    assert empty_result.recommended_outreach_channel == "DIRECT_MAIL"
    assert "in re the estate" in (empty_result.outreach_script_template or "").lower()

def test_title_research_provider():
    provider = TitleResearchProvider()
    assert provider.provider_id == "provider_county_auditor_title"
    assert ResearchArea.TITLE in provider.supported_areas
    
    # 1. Unindexed lookup returns transparent pending status without synthetic deeds
    req = ResearchRequest(
        address="4501 N 28th St, Tacoma, WA 98407",
        area=ResearchArea.TITLE,
        county_id="cty_pierce"
    )
    result = provider.execute(req, context={"decedent": "Harold Vance"})
    
    assert result.apn is not None
    assert result.assessed_value > 0
    assert len(result.deed_chain) == 0
    assert result.tax_status == "PENDING_AUDITOR_RECORDING_INDEX"
    assert result.total_senior_debt == 0.0

    # 2. When authentic deeds are provided in context
    result_with_deeds = provider.execute(req, context={
        "decedent": "Harold Vance",
        "deeds": [
            {
                "instrument_number": "AUD-PIERCE-201804150119",
                "recording_date": "2018-04-15",
                "deed_type": "STATUTORY_WARRANTY_DEED",
                "grantor": "Prior Owner LLC",
                "grantee": "Harold Vance"
            }
        ]
    })
    assert len(result_with_deeds.deed_chain) == 1
    assert result_with_deeds.deed_chain[0].grantee == "Harold Vance"
    assert result_with_deeds.tax_status == "CURRENT (Assessor Certified)"

def test_authority_and_valuation_providers():
    auth_p = AuthorityResearchProvider()
    req_auth = ResearchRequest(case_number="26-4-01992-3", county_id="cty_pierce", area=ResearchArea.AUTHORITY)
    auth_res = auth_p.execute(req_auth, context={"decedent": "Harold Vance"})
    assert auth_res.nonintervention_powers is True
    assert "RCW 11.68" in auth_res.statutory_basis
    assert auth_res.can_execute_psa is True

    val_p = ValuationResearchProvider()
    req_val = ResearchRequest(address="4501 N 28th St, Tacoma, WA 98407", area=ResearchArea.VALUATION)
    val_res = val_p.execute(req_val, context={"senior_debt": 100000.0})
    assert val_res.estimated_market_value > 0
    assert val_res.net_distributable_equity > 0
    assert val_res.target_wholesale_mao > 0

def test_provider_extendability():
    # Verify we can plug in a new custom provider with zero core changes
    class CustomTaxAssessorProvider(BaseResearchProvider):
        @property
        def provider_id(self) -> str:
            return "provider_custom_tax_assessor"
        @property
        def name(self) -> str:
            return "Custom Washington Municipal Assessor Adapter"
        @property
        def version(self) -> str:
            return "1.0.0"
        @property
        def supported_areas(self):
            return [ResearchArea.TITLE]
        @property
        def description(self) -> str:
            return "Custom vendor feed for real-time tax rolls"
        def execute(self, req, context=None):
            return {"tax_delinquent": False, "parcel_status": "EXEMPT"}

    custom_p = CustomTaxAssessorProvider()
    ResearchHubService.register_provider(custom_p)
    
    providers = ResearchHubService.list_providers()
    provider_ids = [p.provider_id for p in providers]
    assert "provider_custom_tax_assessor" in provider_ids

def test_research_hub_service_comprehensive_sweep_and_db_audit():
    db = SessionLocal()
    try:
        opp = db.query(OpportunityModel).first()
        assert opp is not None

        req = ResearchRequest(
            opportunity_id=opp.id,
            area=ResearchArea.COMPREHENSIVE
        )
        dossier = ResearchHubService.execute_research(req, db=db, operator_name="Lead Analyst")
        
        assert dossier.contacts is not None
        assert dossier.title is not None
        assert dossier.authority is not None
        assert dossier.valuation is not None
        assert dossier.overall_confidence > 0.90
        assert len(dossier.summary_notes) > 20

    finally:
        db.close()

def test_api_research_endpoints():
    headers = {
        "x-clerk-user-id": "user_researcher_test",
        "x-clerk-role": "Senior Title & Skip-Trace Specialist"
    }

    # 1. List registered providers
    res_prov = client.get("/api/research/providers")
    assert res_prov.status_code == 200
    providers = res_prov.json()
    assert len(providers) >= 4
    ids = [p["provider_id"] for p in providers]
    assert "provider_skip_trace_core" in ids
    assert "provider_county_auditor_title" in ids

    # 2. Execute Contacts skip-trace with authentic contact inputs
    res_cnt = client.post(
        "/api/research/contacts",
        json={
            "target_name": "Clara Bell",
            "county_id": "cty_pierce",
            "area": "CONTACTS",
            "raw_phones": ["+12534440182"]
        },
        headers=headers
    )
    assert res_cnt.status_code == 200
    cnt_data = res_cnt.json()
    assert cnt_data["contacts"] is not None
    assert len(cnt_data["contacts"]["phones"]) == 1
    assert cnt_data["contacts"]["primary_phone"] == "+12534440182"
    assert cnt_data["contacts"]["recommended_outreach_channel"] == "PHONE_CALL"

    # Also test empty inquiry returns honest empty direct-mail state without fake 555 numbers
    res_empty = client.post(
        "/api/research/contacts",
        json={"target_name": "Unknown Fiduciary", "county_id": "cty_pierce", "area": "CONTACTS"},
        headers=headers
    )
    assert res_empty.status_code == 200
    assert len(res_empty.json()["contacts"]["phones"]) == 0
    assert res_empty.json()["contacts"]["primary_phone"] is None
    assert res_empty.json()["contacts"]["recommended_outreach_channel"] == "DIRECT_MAIL"

    # 3. Execute Title deed chain search
    res_title = client.post(
        "/api/research/title",
        json={"address": "1200 Pacific Ave, Tacoma, WA 98402", "county_id": "cty_pierce", "area": "TITLE"},
        headers=headers
    )
    assert res_title.status_code == 200
    title_data = res_title.json()
    assert title_data["title"]["tax_status"] == "PENDING_AUDITOR_RECORDING_INDEX"
    assert len(title_data["title"]["deed_chain"]) == 0

    # 4. Fetch Opportunity Dossier
    opp = client.get("/api/opportunities", headers=headers).json()[0]
    res_dos = client.get(f"/api/research/{opp['id']}/dossier", headers=headers)
    assert res_dos.status_code == 200
    dos_data = res_dos.json()
    assert dos_data["contacts"] is not None
    assert dos_data["title"] is not None

    # 5. Workbench enriched with contact_summary
    res_wb = client.get(f"/api/opportunities/{opp['id']}/workbench", headers=headers)
    assert res_wb.status_code == 200
    wb_data = res_wb.json()
    assert "contact_summary" in wb_data
    assert "primary_phone" in wb_data["contact_summary"]
    assert "line_type" in wb_data["contact_summary"]
