"""
Tests for Phase 1 Applications Endpoints:
- Dashboard executive metrics & 6 queues
- Opportunity Workbench 6-domain summary
- POF generation (HTML & CRM JSON)
- AI Investigator multi-agent Q&A
- Client Portal feed & telemetry feedback
"""

import pytest
from fastapi.testclient import TestClient
from gieni_os.api.main import app
from gieni_os.database.connection import get_db, SessionLocal
from gieni_os.database.models import CountyModel, ProbateCaseModel, OpportunityModel

client = TestClient(app, headers={
    "x-clerk-user-id": "user_operator_lead",
    "x-clerk-role": "Platform Admin"
})

@pytest.fixture(scope="module")
def setup_seed_data():
    db = SessionLocal()
    try:
        county = db.query(CountyModel).filter(CountyModel.id == "county-pierce-app").first()
        if not county:
            county = CountyModel(id="county-pierce-app", name="Pierce", state="WA", tier="TIER_1", status="ACTIVE")
            db.add(county)
            db.commit()

        case = db.query(ProbateCaseModel).filter(ProbateCaseModel.case_number == "26-4-09999-1").first()
        if not case:
            case = ProbateCaseModel(
                id="case-app-test-1",
                case_number="26-4-09999-1",
                county_id="county-pierce-app",
                decedent="Margaret Rose Albright",
                status="OPEN"
            )
            db.add(case)
            db.commit()

        opp = db.query(OpportunityModel).filter(OpportunityModel.id == "opp-app-test-1").first()
        if not opp:
            opp = OpportunityModel(
                id="opp-app-test-1",
                case_id=case.id,
                county_id="county-pierce-app",
                workflow_stage="QC",
                priority="Priority A",
                authority_status="Tier 1: Court Certified",
                score=92
            )
            db.add(opp)
        else:
            opp.workflow_stage = "QC"
        db.commit()

        yield opp
    finally:
        db.close()

def test_dashboard_metrics_and_queues(setup_seed_data):
    # 1. Executive Metrics
    res = client.get("/api/dashboard/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert "cases_processed" in metrics
    assert "authority_accuracy_pct" in metrics
    assert "qc_pass_rate_pct" in metrics
    assert "delivered_opportunities" in metrics
    assert "active_counties" in metrics
    assert metrics["total_cases"] >= 1

    # 2. 6 Operational Queues
    qres = client.get("/api/dashboard/queues")
    assert qres.status_code == 200
    queues = qres.json()
    assert "property_queue" in queues
    assert "ownership_queue" in queues
    assert "authority_queue" in queues
    assert "qc_queue" in queues
    assert "exception_queue" in queues
    assert "delivery_queue" in queues
    assert len(queues["qc_queue"]) >= 1

def test_opportunity_workbench(setup_seed_data):
    opp_id = setup_seed_data.id
    res = client.get(f"/api/opportunities/{opp_id}/workbench")
    assert res.status_code == 200
    data = res.json()
    
    assert "opportunity" in data
    assert "property_summary" in data
    assert "ownership_summary" in data
    assert "authority_summary" in data
    assert "risk_summary" in data
    assert "evidence_summary" in data
    assert "score_summary" in data
    assert "recommended_action" in data

    assert data["property_summary"]["apn"]
    assert data["ownership_summary"]["net_distributable_equity"] > 0
    assert data["authority_summary"]["statutory_basis"]
    assert data["score_summary"]["composite_viability_score"] == 92

def test_pof_generation_and_export(setup_seed_data):
    opp_id = setup_seed_data.id
    
    # Generate POF
    res = client.post(f"/api/opportunities/{opp_id}/pof/generate")
    assert res.status_code == 200
    data = res.json()
    assert "html_dossier" in data
    assert "crm_payload" in data
    assert "<!DOCTYPE html>" in data["html_dossier"]
    assert data["crm_payload"]["opportunity_id"] == opp_id

    # Direct HTML preview
    hres = client.get(f"/api/opportunities/{opp_id}/pof/html")
    assert hres.status_code == 200
    assert "text/html" in hres.headers["content-type"]

    # Direct JSON preview
    jres = client.get(f"/api/opportunities/{opp_id}/pof/json")
    assert jres.status_code == 200
    assert jres.json()["opportunity_id"] == opp_id

def test_ai_investigator(setup_seed_data):
    opp_id = setup_seed_data.id
    
    # 1. Why Priority A?
    res1 = client.post("/api/ai/investigate", json={"opportunity_id": opp_id, "query": "Why is this Priority A?"})
    assert res1.status_code == 200
    d1 = res1.json()
    assert "Priority" in d1["narrative"]
    assert len(d1["citations"]) > 0
    assert len(d1["recommendations"]) > 0

    # 2. Who controls disposition?
    res2 = client.post("/api/ai/investigate", json={"opportunity_id": opp_id, "query": "Who controls disposition?"})
    assert res2.status_code == 200
    d2 = res2.json()
    assert "Personal Representative" in d2["narrative"]

    # 3. Explain authority path
    res3 = client.post("/api/ai/investigate", json={"opportunity_id": opp_id, "query": "Explain authority path"})
    assert res3.status_code == 200
    d3 = res3.json()
    assert "RCW" in d3["narrative"]

def test_client_portal(setup_seed_data):
    opp_id = setup_seed_data.id
    
    # Dashboard
    dres = client.get("/api/client/dashboard")
    assert dres.status_code == 200
    assert "active_opportunities" in dres.json()

    # Feed
    fres = client.get("/api/client/feed")
    assert fres.status_code == 200
    assert isinstance(fres.json(), list)

    # Telemetry feedback submission
    feedback_payload = {
        "opportunity_id": opp_id,
        "stage": "OFFER",
        "client_name": "Sound Acquisition Group",
        "notes": "Spoke with PR, submitting $420,000 cash offer with 14-day close.",
        "offer_amount": 420000.0
    }
    fb_res = client.post("/api/client/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["status"] == "SUCCESS"
    assert fb_data["telemetry_recorded"] is True
