"""
End-to-end verification of all interactive UI actions & API wiring:
- POF HTML dossier delivery (/api/pof/{id}/html and /api/opportunities/{id}/pof/html)
- Opportunity Workbench operator actions: approve, reject, research, send-qc
- AI Investigator flexible query payloads (query / question aliases)
- Opportunity and County enrichment models
"""

import pytest
from fastapi.testclient import TestClient
from gieni_os.api.main import app

from gieni_os.database.connection import SessionLocal
from gieni_os.database.models import OpportunityModel

client = TestClient(app)

def test_pof_html_direct_and_alias():
    headers = {"x-clerk-user-id": "user_operator_lead"}
    # Direct alias
    res1 = client.get("/api/pof/opp_001/html", headers=headers)
    assert res1.status_code == 200
    assert "PROBATE OPPORTUNITY FILE" in res1.text or "<html" in res1.text

    # Route under opportunities
    res2 = client.get("/api/opportunities/opp_001/pof/html", headers=headers)
    assert res2.status_code == 200
    assert "PROBATE OPPORTUNITY FILE" in res2.text or "<html" in res2.text

def test_workbench_operator_actions():
    db = SessionLocal()
    try:
        opp = db.query(OpportunityModel).filter(OpportunityModel.id == "opp_001").first()
        if opp:
            opp.workflow_stage = "NEW"
            db.commit()
    finally:
        db.close()

    headers = {
        "x-clerk-user-id": "user_operator_lead",
        "x-clerk-role": "Senior Research Analyst"
    }

    # 1. Send to QC
    qc_res = client.post("/api/opportunities/opp_001/send-qc", json={"notes": "Routing deal to QC gate"}, headers=headers)
    assert qc_res.status_code == 200
    assert qc_res.json()["workflow_stage"] == "QC"

    # 2. Approve deal
    app_res = client.post("/api/opportunities/opp_001/approve", json={"notes": "Sign-off verified"}, headers=headers)
    assert app_res.status_code == 200
    assert app_res.json()["workflow_stage"] in ["READY", "DELIVERED"]

    # 3. Request research
    res_res = client.post("/api/opportunities/opp_001/research", json={"notes": "Need title deed chain check"}, headers=headers)
    assert res_res.status_code == 200
    assert res_res.json()["workflow_stage"] == "OWNERSHIP"

    # 4. Reject deal
    rej_res = client.post("/api/opportunities/opp_001/reject", json={"notes": "Title clouded with senior IRS lien"}, headers=headers)
    assert rej_res.status_code == 200
    assert rej_res.json()["workflow_stage"] == "EXCEPTION"

def test_ai_investigator_payload_resilience():
    # Using 'question' field
    res_q = client.post("/api/ai/investigate", json={
        "opportunity_id": "opp_001",
        "question": "Who controls this property?"
    })
    assert res_q.status_code == 200
    data_q = res_q.json()
    assert "narrative" in data_q
    assert data_q["confidence_score"] > 0.8
    assert "ControlAgent" in data_q["connected_agents"]

    # Using 'query' field
    res_query = client.post("/api/ai/investigate", json={
        "opportunity_id": "opp_001",
        "query": "Why is this Priority A?"
    })
    assert res_query.status_code == 200
    data_query = res_query.json()
    assert "narrative" in data_query
    assert "ScoringAgent" in data_query["connected_agents"]

def test_opportunities_list_enrichment():
    headers = {"x-clerk-user-id": "user_operator_lead"}
    res = client.get("/api/opportunities", headers=headers)
    assert res.status_code == 200
    opps = res.json()
    assert len(opps) > 0
    first = opps[0]
    assert "estate_name" in first
    assert "county_name" in first
    assert "case_number" in first

def test_county_board_resilience():
    res = client.get("/api/dashboard/county-board")
    assert res.status_code == 200
    board = res.json()
    assert len(board) > 0
    for c in board:
        assert "name" in c
        assert "expansion_score" in c
        assert "median_home_price" in c
        assert "recommendation" in c
