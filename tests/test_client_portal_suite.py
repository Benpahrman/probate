"""
Comprehensive Test Suite for Phase 2: Client Portal (Revenue Product)
Tests:
- Partner Profile & Delivery Quotas
- Client Feed Filtering & Sorting
- Client Opportunity Detail Dossier
- CRM Webhook Export
- Closed-Loop Disposition Telemetry & Feedback
- Telemetry Conversion Statistics
"""

import pytest
from fastapi.testclient import TestClient
from gieni_os.api.main import app
from gieni_os.database.connection import SessionLocal
from gieni_os.database.models import CountyModel, ProbateCaseModel, OpportunityModel, ExceptionModel

client = TestClient(app, headers={
    "x-clerk-user-id": "user_partner_sound",
    "x-clerk-org-id": "org_sound_capital",
    "x-clerk-role": "org:admin"
})

@pytest.fixture(scope="module")
def setup_client_data():
    db = SessionLocal()
    try:
        county = db.query(CountyModel).filter(CountyModel.id == "county-pierce-client").first()
        if not county:
            county = CountyModel(id="county-pierce-client", name="Pierce", state="WA", tier="TIER_1", status="ACTIVE")
            db.add(county)
            db.commit()

        case = db.query(ProbateCaseModel).filter(ProbateCaseModel.case_number == "26-4-07777-2").first()
        if not case:
            case = ProbateCaseModel(
                id="case-client-test-1",
                case_number="26-4-07777-2",
                county_id="county-pierce-client",
                decedent="Arthur Pendelton Vance",
                status="OPEN"
            )
            db.add(case)
            db.commit()

        opp = db.query(OpportunityModel).filter(OpportunityModel.id == "opp-client-test-1").first()
        if not opp:
            opp = OpportunityModel(
                id="opp-client-test-1",
                case_id=case.id,
                county_id="county-pierce-client",
                workflow_stage="DELIVERED",
                priority="Priority A",
                authority_status="Tier 1: Court Certified",
                score=95
            )
            db.add(opp)
            db.commit()

        yield opp
    finally:
        db.close()

def test_partner_profile(setup_client_data):
    res = client.get("/api/client/partner-profile")
    assert res.status_code == 200
    data = res.json()
    assert "partner_name" in data
    assert "exclusive_county" in data
    assert "monthly_quota_target" in data
    assert "quota_progress_pct" in data
    assert data["jurisdiction_lock"] is True

def test_client_feed_and_filtering(setup_client_data):
    # 1. All
    res = client.get("/api/client/feed?filter_type=ALL")
    assert res.status_code == 200
    feed = res.json()
    assert len(feed) > 0
    item = feed[0]
    assert "net_equity" in item
    assert "target_mao" in item
    assert "authority_tier" in item
    assert "primary_decision_maker" in item
    assert "funnel_stage" in item

    # 2. Priority A filter
    res_a = client.get("/api/client/feed?filter_type=PRIORITY_A")
    assert res_a.status_code == 200
    for it in res_a.json():
        assert "A" in it["priority_tier"]

def test_client_opportunity_detail(setup_client_data):
    opp_id = setup_client_data.id
    res = client.get(f"/api/client/opportunity/{opp_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["opportunity_id"] == opp_id
    assert "property" in detail
    assert "equity_waterfall" in detail
    assert "contact_dossier" in detail
    assert "authority_powers" in detail
    assert detail["authority_powers"]["can_execute_psa"] is True
    assert "telemetry_history" in detail

def test_crm_export(setup_client_data):
    opp_id = setup_client_data.id

    # 1. Omitting webhook_url returns 400 Bad Request
    payload_invalid = {
        "opportunity_id": opp_id,
        "crm_platform": "GoHighLevel"
    }
    res_err = client.post("/api/client/export/crm", json=payload_invalid)
    assert res_err.status_code == 400
    assert "Registered webhook URL is required" in res_err.json()["detail"]

    # 2. Providing registered webhook_url returns 200 DISPATCHED
    payload_valid = {
        "opportunity_id": opp_id,
        "crm_platform": "GoHighLevel",
        "webhook_url": "https://api.soundcapital.com/webhooks/partner-crm"
    }
    res = client.post("/api/client/export/crm", json=payload_valid)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "DISPATCHED"
    assert data["crm_platform"] == "GoHighLevel"
    assert data["webhook_url"] == "https://api.soundcapital.com/webhooks/partner-crm"
    assert "payload" in data
    assert data["payload"]["opportunity_id"] == opp_id

def test_feedback_and_telemetry_loop(setup_client_data):
    opp_id = setup_client_data.id

    # 1. Submit Offer
    offer_submission = {
        "opportunity_id": opp_id,
        "stage": "OFFER",
        "client_name": "Sound Capital Acquisitions",
        "notes": "Met with Personal Representative at property. Made cash offer.",
        "offer_amount": 475000.0,
        "estimated_close_days": 10
    }
    res = client.post("/api/client/feedback", json=offer_submission)
    assert res.status_code == 200
    fb = res.json()
    assert fb["status"] == "SUCCESS"
    assert fb["stage"] == "OFFER"
    assert fb["offer_amount"] == 475000.0

    # 2. Submit Contract
    contract_submission = {
        "opportunity_id": opp_id,
        "stage": "CONTRACT",
        "client_name": "Sound Capital Acquisitions",
        "notes": "Mutual acceptance! Escrow opened with Fidelity National Title.",
        "offer_amount": 475000.0,
        "estimated_close_days": 14
    }
    c_res = client.post("/api/client/feedback", json=contract_submission)
    assert c_res.status_code == 200
    assert c_res.json()["stage"] == "CONTRACT"

    # 3. Check Telemetry Statistics
    t_res = client.get("/api/client/telemetry/stats")
    assert t_res.status_code == 200
    stats = t_res.json()
    assert stats["offer_count"] >= 1
    assert stats["contract_count"] >= 1
    assert stats["total_offer_volume"] > 0
    assert "win_rate_pct" in stats
