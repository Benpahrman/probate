"""
Integration Test Suite: Production Backend APIs & Harvesters
Verifies:
1. Live County Harvesters (LinxHarvester, AuditorHarvester, LegalNoticesHarvester)
2. Opportunity QC 6-Gate Audit & /qc route alias
3. Deal Room CRM direct dispatch (/export-crm)
4. Live Municipal County Radar (/dashboard/county-board)
5. AI Jurisprudential Investigator (/ai/investigate)
"""

import uuid
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.jurisdiction import County
from app.models.identity import Person
from app.models.property import ProbateCase, Property
from app.models.intelligence import Opportunity
from app.models.evidence import TaskException
from app.models.enums import LifecycleStage, PriorityTier, PropertyClass
from app.workers.harvesters.linx_harvester import LinxHarvester
from app.workers.harvesters.auditor_harvester import AuditorHarvester
from app.workers.harvesters.legal_notices_harvester import LegalNoticesHarvester

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_linx_harvester_salvaged():
    """LinxHarvester returns authentic Pierce County probate dockets."""
    dockets = LinxHarvester.harvest(days_back=14)
    assert len(dockets) > 0
    for d in dockets:
        assert d.case_number.startswith("26-4-")
        assert "Vance" not in (d.decedent or "")
        assert d.county_id == "cty_pierce"


def test_auditor_harvester_salvaged():
    """AuditorHarvester extracts non-probate filings (LOPA, TODD, CPA)."""
    dockets = AuditorHarvester.harvest(county_id="cty_pierce", days_back=14)
    assert len(dockets) > 0
    for d in dockets:
        assert d.channel.value == "AUDITOR_NON_PROBATE"
        assert d.instrument_number is not None
        assert "Vance" not in (d.decedent or "")


def test_legal_notices_harvester_salvaged():
    """LegalNoticesHarvester parses Notice to Creditors."""
    dockets = LegalNoticesHarvester.harvest(county_id="cty_king", days_back=14)
    assert len(dockets) > 0
    for d in dockets:
        assert d.channel.value == "NOTICE_TO_CREDITORS"
        assert "Vance" not in (d.decedent or "")


def test_county_radar_live_endpoint():
    """GET /api/v1/dashboard/county-board returns real-time jurisdiction intelligence."""
    res = client.get("/api/v1/dashboard/county-board")
    assert res.status_code == 200
    board = res.json()
    assert isinstance(board, list)
    assert len(board) > 0
    first = board[0]
    assert "name" in first
    assert "expansion_score" in first
    assert "court_portal" in first


def test_ai_investigator_statutory_endpoint():
    """POST /api/v1/ai/investigate answers RCW Title 11 jurisprudence queries."""
    res = client.post(
        "/api/v1/ai/investigate",
        json={"prompt": "Explain nonintervention powers under RCW 11.68"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "RCW 11.68.011" in data["statutory_citations"]
    assert len(data["response"]) > 0


def test_opportunity_crm_export_with_webhook():
    """POST /api/v1/opportunities/{id}/export-crm dispatches deal to webhook."""
    db: Session = SessionLocal()
    try:
        county = db.query(County).filter(County.county_fips == "53053").first()
        if not county:
            county = County(
                county_fips="53053",
                name="Pierce",
                state="WA",
                court_software_vendor="LINX"
            )
            db.add(county)
            db.flush()

        decedent = Person(first_name="Margaret", last_name="Albright", is_deceased=True)
        db.add(decedent)
        db.flush()

        case = ProbateCase(
            county_id=county.county_id,
            case_number=f"26-4-TEST-CRM-{uuid.uuid4().hex[:6]}",
            filing_date=date.today(),
            decedent_id=decedent.person_id,
            invariant_hash=f"test-inv-hash-crm-{uuid.uuid4().hex[:8]}"
        )
        db.add(case)
        db.flush()

        prop = Property(
            case_id=case.case_id,
            county_id=county.county_id,
            apn=f"022{uuid.uuid4().hex[:7]}",
            street="4812 N 16th St",
            city="Tacoma",
            state="WA",
            zip_code="98406",
            pas_score=95.0
        )
        db.add(prop)
        db.flush()

        opp = Opportunity(
            case_id=case.case_id,
            property_id=prop.property_id,
            lifecycle_stage=LifecycleStage.QC_CERTIFIED,
            composite_viability_score=92,
            is_qc_certified=True
        )
        db.add(opp)
        db.commit()
        opp_id = opp.opportunity_id

        # 1. Missing webhook returns 400
        res_fail = client.post(f"/api/v1/opportunities/{opp_id}/export-crm", json={})
        assert res_fail.status_code == 400

        # 2. Valid webhook dispatches cleanly
        from unittest.mock import patch, MagicMock
        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.status_code = 200

        with patch("httpx.Client.post", return_value=mock_resp):
            res_ok = client.post(
                f"/api/v1/opportunities/{opp_id}/export-crm",
                json={"webhook_url": "https://api.crm.example/webhook"}
            )
            assert res_ok.status_code == 200
            data = res_ok.json()
            assert data["status"] == "SUCCESS"
            assert data["response_code"] == 200
    finally:
        db.close()


def test_qc_gate_audit_alias():
    """POST /api/v1/opportunities/{id}/qc executes 6-gate audit."""
    db: Session = SessionLocal()
    try:
        opp = db.query(Opportunity).first()
        if opp:
            res = client.post(f"/api/v1/opportunities/{opp.opportunity_id}/qc")
            assert res.status_code == 200
            data = res.json()
            assert "is_fully_certified" in data
            assert "overall_passed" in data
    finally:
        db.close()


def test_honeybadger_telemetry_integration():
    """Verifies that Honeybadger is configured and mounted in the FastAPI ASGI middleware stack."""
    from honeybadger import honeybadger, contrib
    from app.core.config import settings

    assert settings.HONEYBADGER_API_KEY is not None
    assert honeybadger.config.api_key == settings.HONEYBADGER_API_KEY
    assert any(m.cls == contrib.ASGIHoneybadger for m in app.user_middleware)
