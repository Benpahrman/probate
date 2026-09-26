import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.workers.ingestion_worker import MunicipalIngestionWorker
from app.models.intelligence import Opportunity
from app.models.evidence import TaskException
from app.models.enums import LifecycleStage, ExceptionPriority

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"


def test_worker_ingestion_and_api_flow():
    """Verifies that the Playwright worker commits records at stage DISCOVERED
    and that API v1 endpoints can list, inspect, and evaluate them.
    """
    county_fips = "53067"
    worker = MunicipalIngestionWorker(county_fips=county_fips)

    # 1. Process simulated raw dockets
    raw_dockets = [{
        "case_number": f"2026-PR-{uuid.uuid4().hex[:6]}",
        "filing_date": date.today(),
        "decedent_name": "SARAH EMILY CONNOR",
        "petitioner_name": "JOHN CONNOR",
        "attorney_name": "SILBERMAN LEGAL",
        "docket_url": "https://test.court/docket/123",
        "pdf_content": b"%PDF-1.4 Mock Court Petition Binary Buffer..."
    }]
    case_ids = worker.process_and_commit(raw_dockets)
    assert len(case_ids) == 1

    # 2. Query Opportunity through API
    response = client.get("/api/v1/opportunities", params={"stage": "DISCOVERED", "limit": 500})
    assert response.status_code == 200
    opps = response.json()
    assert len(opps) >= 1

    target_opp = [o for o in opps if o["case_id"] == str(case_ids[0])][0]
    assert target_opp["lifecycle_stage"] == "DISCOVERED"


    # 3. Advance to PROPERTY_IDENTIFIED
    trans_res = client.post(
        f"/api/v1/opportunities/{target_opp['opportunity_id']}/transition",
        json={"target_stage": "PROPERTY_IDENTIFIED"}
    )
    assert trans_res.status_code == 200
    assert trans_res.json()["lifecycle_stage"] == "PROPERTY_IDENTIFIED"

    # 4. Trigger Quality Control Audit
    qc_res = client.post(f"/api/v1/opportunities/{target_opp['opportunity_id']}/execute-qc")
    assert qc_res.status_code == 200
    qc_data = qc_res.json()
    assert qc_data["is_fully_certified"] is True
    assert qc_data["current_lifecycle_stage"] == "QC_CERTIFIED"
    assert qc_data["composite_viability_score"] >= 60


def test_illegal_stage_transition_api_rejection():
    """Verify API returns 400 when attempting an illegal state skip."""
    db: Session = SessionLocal()
    opp = db.query(Opportunity).first()
    db.close()

    if opp:
        response = client.post(
            f"/api/v1/opportunities/{opp.opportunity_id}/transition",
            json={"target_stage": "CLOSED_WON"}  # Illegal leap from early stage
        )
        assert response.status_code == 400
        assert "Illegal state transition" in response.json()["detail"]


def test_list_probate_cases_api():
    """Verify cases list endpoint returns valid CaseResponse objects."""
    response = client.get("/api/v1/cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "case_number" in data[0]
        assert "county_fips" in data[0]
        assert "decedent_name" in data[0]


def test_exceptions_api_list_and_resolve():
    """Verify listing open exceptions and resolving an exception ticket."""
    db: Session = SessionLocal()
    opp = db.query(Opportunity).first()
    assert opp is not None, "Opportunity needed to test exceptions"

    # Create an open test exception
    test_ticket = TaskException(
        case_id=opp.case_id,
        failed_gate=2,
        exception_type="Gate 2 Attribution Cloud",
        priority=ExceptionPriority.HIGH,
        status="OPEN",
        resolution_notes="Requires deed verification"
    )
    db.add(test_ticket)
    db.commit()
    db.refresh(test_ticket)
    ticket_id = str(test_ticket.exception_id)
    db.close()

    # Query open exceptions
    res = client.get("/api/v1/exceptions")
    assert res.status_code == 200
    open_list = res.json()
    matched = [e for e in open_list if e["exception_id"] == ticket_id]
    assert len(matched) == 1
    assert matched[0]["status"] == "OPEN"

    # Resolve exception ticket with automated 6-gate re-audit
    resolve_res = client.post(
        f"/api/v1/exceptions/{ticket_id}/resolve?resolution_text=Title+cleared+via+deed+record"
    )
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["re_audited"] is True
    assert "audit_summary" in res_data
    assert res_data["audit_summary"]["is_fully_certified"] is True

    # Confirm status is updated to RESOLVED
    db2 = SessionLocal()
    resolved = db2.query(TaskException).filter(TaskException.exception_id == uuid.UUID(ticket_id)).first()
    assert resolved is not None
    assert resolved.status == "RESOLVED"
    assert resolved.resolution_notes is not None
    assert "Title cleared" in resolved.resolution_notes
    db2.close()


def test_deterministic_parcel_and_equity_cascade():
    """WF-INTAKE-02: Verifies that docket ingestion triggers deterministic PAS and equity waterfall."""
    worker = MunicipalIngestionWorker(county_fips="53053")
    raw = [{
        "case_number": f"26-4-CASCADE-{uuid.uuid4().hex[:6]}",
        "filing_date": date.today(),
        "decedent_name": "ELEANOR ROOSEVELT",
        "petitioner_name": "FRANKLIN ROOSEVELT",
        "attorney_name": "CAMPBELL LAW",
        "docket_url": "https://linx.co.pierce.wa.us/test",
        "pdf_content": b"PDF_SAMPLE"
    }]
    case_ids = worker.process_and_commit(raw)
    assert len(case_ids) == 1

    db = SessionLocal()
    opp = db.query(Opportunity).filter(Opportunity.case_id == case_ids[0]).first()
    assert opp is not None
    prop = opp.property
    assert prop is not None
    assert float(prop.pas_score) >= 70.0  # PAS Engine verification

    # Ownership encumbrance waterfall check
    assert prop.ownership_assessment is not None
    assert float(prop.ownership_assessment.net_equity) > 0.0
    assert float(prop.ownership_assessment.total_encumbrances) > 0.0
    assert float(prop.ownership_assessment.equity_pct) > 0.30
    db.close()

