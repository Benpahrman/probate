"""
Comprehensive Test Suite: Clerk Multi-Tenancy Isolation & 5 Modular Applications
Tests:
- Zero Custom Auth: Clerk claims normalization (x-clerk-user-id, x-clerk-org-id, x-clerk-role)
- Tenancy Isolation: Clerk Org -> County Contract -> Opportunity Visibility
- All 5 Modular App Route Mounts (/ops, /workbench, /investigator, /portal, /counties, /)
- Static application assets (/ops/app.js, /workbench/app.js, etc.)
- Multi-agent AI Investigator & County Intelligence radar
"""

import pytest
from fastapi.testclient import TestClient
from gieni_os.api.main import app
from gieni_os.database.connection import SessionLocal
from gieni_os.database.models import CountyModel, OpportunityModel, ProbateCaseModel
from datetime import datetime

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_tenancy_test_data():
    db = SessionLocal()
    try:
        # Ensure counties exist
        for cid, name in [("cty_thurston", "Thurston"), ("cty_pierce", "Pierce"), ("cty_king", "King")]:
            if not db.query(CountyModel).filter(CountyModel.id == cid).first():
                db.add(CountyModel(id=cid, name=name, state="WA", status="ACTIVE", tier="TIER_1"))
        
        # Ensure test cases and opportunities exist in both Thurston and Pierce
        th_case = db.query(ProbateCaseModel).filter(ProbateCaseModel.id == "case_tenancy_th").first()
        if not th_case:
            th_case = ProbateCaseModel(
                id="case_tenancy_th",
                county_id="cty_thurston",
                case_number="26-4-00101-34",
                decedent="Eleanor Vance",
                status="OPEN"
            )
            db.add(th_case)

        pc_case = db.query(ProbateCaseModel).filter(ProbateCaseModel.id == "case_tenancy_pc").first()
        if not pc_case:
            pc_case = ProbateCaseModel(
                id="case_tenancy_pc",
                county_id="cty_pierce",
                case_number="26-4-00202-53",
                decedent="Robert Sterling",
                status="OPEN"
            )
            db.add(pc_case)

        db.commit()

        # Opportunities in Thurston and Pierce
        th_opp = db.query(OpportunityModel).filter(OpportunityModel.id == "opp_tenancy_th").first()
        if not th_opp:
            th_opp = OpportunityModel(
                id="opp_tenancy_th",
                case_id="case_tenancy_th",
                county_id="cty_thurston",
                workflow_stage="DELIVERED",
                priority="A",
                authority_status="RESOLVED",
                score=95.0
            )
            db.add(th_opp)

        pc_opp = db.query(OpportunityModel).filter(OpportunityModel.id == "opp_tenancy_pc").first()
        if not pc_opp:
            pc_opp = OpportunityModel(
                id="opp_tenancy_pc",
                case_id="case_tenancy_pc",
                county_id="cty_pierce",
                workflow_stage="DELIVERED",
                priority="A",
                authority_status="RESOLVED",
                score=92.0
            )
            db.add(pc_opp)

        db.commit()
    finally:
        db.close()

# ---------------------------------------------------------
# Test 1: Modular Application Route Mounts
# ---------------------------------------------------------

def test_launchpad_root_mount():
    res = client.get("/")
    assert res.status_code == 200
    assert "GIENI OS" in res.text
    assert "Operations Center" in res.text
    assert "Opportunity Workbench" in res.text

def test_ops_center_mount():
    res = client.get("/ops")
    assert res.status_code == 200
    assert "Operations Center" in res.text
    res_js = client.get("/ops/app.js")
    assert res_js.status_code == 200

def test_workbench_mount():
    res = client.get("/workbench")
    assert res.status_code == 200
    assert "Opportunity Workbench" in res.text
    res_js = client.get("/workbench/app.js")
    assert res_js.status_code == 200

def test_investigator_mount():
    res = client.get("/investigator")
    assert res.status_code == 200
    assert "AI Investigator" in res.text
    res_js = client.get("/investigator/app.js")
    assert res_js.status_code == 200

def test_client_portal_mount():
    res = client.get("/portal")
    assert res.status_code == 200
    assert "Client Portal" in res.text or "Partner Deal Room" in res.text
    res_js = client.get("/portal/app.js")
    assert res_js.status_code == 200

def test_county_intelligence_mount():
    res = client.get("/counties")
    assert res.status_code == 200
    assert "County Intelligence" in res.text
    res_js = client.get("/counties/app.js")
    assert res_js.status_code == 200

# ---------------------------------------------------------
# Test 2: Clerk Multi-Tenancy Isolation
# ---------------------------------------------------------

def test_clerk_org_partner_profile_thurston():
    res = client.get("/api/client/partner-profile", headers={
        "x-clerk-org-id": "org_nw_acquisitions",
        "x-clerk-role": "org:admin"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["county_contract"] == "Thurston"
    assert data["partner_name"] == "Acquisitions Northwest"

def test_clerk_org_partner_profile_pierce():
    res = client.get("/api/client/partner-profile", headers={
        "x-clerk-org-id": "org_sound_capital",
        "x-clerk-role": "org:admin"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["county_contract"] == "Pierce"
    assert data["partner_name"] == "Sound Capital"

def test_clerk_org_feed_isolation_strictness():
    """Verify that Thurston contracted client NEVER sees Pierce opportunities"""
    res_th = client.get("/api/client/feed", headers={
        "x-clerk-org-id": "org_nw_acquisitions",
        "x-clerk-role": "org:admin"
    })
    assert res_th.status_code == 200
    deals_th = res_th.json()
    # Check all returned deals belong to Thurston
    for deal in deals_th:
        assert deal["id"] != "opp_tenancy_pc"
        if "county" in deal:
            assert deal["county"] == "Thurston"

    """Verify that Pierce contracted client NEVER sees Thurston opportunities"""
    res_pc = client.get("/api/client/feed", headers={
        "x-clerk-org-id": "org_sound_capital",
        "x-clerk-role": "org:admin"
    })
    assert res_pc.status_code == 200
    deals_pc = res_pc.json()
    for deal in deals_pc:
        assert deal["id"] != "opp_tenancy_th"
        if "county" in deal:
            assert deal["county"] == "Pierce"

# ---------------------------------------------------------
# Test 3: AI Investigator Endpoint
# ---------------------------------------------------------

def test_ai_investigate_priority():
    res = client.post("/api/ai/investigate", json={
        "opportunity_id": "opp_tenancy_th",
        "query": "Why is this Priority A?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "narrative" in data
    assert len(data["citations"]) > 0
    assert len(data["connected_agents"]) > 0
    assert data["confidence_score"] >= 0.90

def test_ai_investigate_authority_path():
    res = client.post("/api/ai/investigate", json={
        "opportunity_id": "opp_tenancy_th",
        "query": "Explain authority path and RCW statutes"
    })
    assert res.status_code == 200
    data = res.json()
    assert "11.68" in data["narrative"] or "Nonintervention" in data["narrative"]
    assert "AuthorityAgent" in data["connected_agents"]

# ---------------------------------------------------------
# Test 4: County Board Scaling Radar
# ---------------------------------------------------------

def test_county_board_expansion_metrics():
    res = client.get("/api/dashboard/county-board")
    assert res.status_code == 200
    board = res.json()
    assert len(board) >= 3
    for c in board:
        assert "expansion_score" in c
        assert "median_home_price" in c
        assert "court_portal" in c
        assert "recommendation" in c

def test_unauthenticated_requests_fail_401():
    # Fresh unauthenticated client without any headers
    from fastapi.testclient import TestClient
    unauthed_client = TestClient(app)
    res = unauthed_client.get("/api/client/partner-profile")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

def test_unknown_org_id_fails_403():
    res = client.get("/api/client/partner-profile", headers={
        "x-clerk-org-id": "org_uncontracted_random",
        "x-clerk-role": "org:admin"
    })
    assert res.status_code == 403
    assert "active county contract" in res.json()["detail"]

