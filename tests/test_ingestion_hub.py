"""
Unit & Integration Tests for Municipal Ingestion & Docket Harvester Layer:
- Harvesters: LinxHarvester, LegalNoticesHarvester, AuditorHarvester
- Pipeline: IngestionPipeline deduplication, opportunity auto-init, audit logging
- API Endpoints:
  - POST /api/ingestion/harvest
  - POST /api/ingestion/bulk-import
  - GET  /api/ingestion/channels
  - GET  /api/ingestion/stats
"""

import pytest
from fastapi.testclient import TestClient
from gieni_os.api.main import app
from gieni_os.database.connection import SessionLocal
from gieni_os.database.models import ProbateCaseModel, OpportunityModel
from gieni_os.ingestion.models import ScrapedDocket, FilingChannel, HarvestRequest, BulkImportRequest
from gieni_os.ingestion.harvesters.linx_harvester import LinxHarvester
from gieni_os.ingestion.harvesters.legal_notices_harvester import LegalNoticesHarvester
from gieni_os.ingestion.harvesters.auditor_harvester import AuditorHarvester
from gieni_os.ingestion.pipeline import IngestionPipeline

client = TestClient(app)

import pytest

@pytest.mark.skip(reason="Synthetic data generation removed per Rule §4")
def test_linx_harvester():
    dockets = LinxHarvester.harvest(days_back=7)
    assert len(dockets) > 0
    for d in dockets:
        assert d.county_id == "cty_pierce"
        assert d.channel == FilingChannel.SUPERIOR_COURT_DOCKET
        assert d.case_number.startswith("26-4-")
        assert d.decedent is not None

def test_legal_notices_harvester():
    # King County (Seattle DJC)
    king_dockets = LegalNoticesHarvester.harvest(county_id="cty_king", days_back=7)
    assert len(king_dockets) > 0
    for d in king_dockets:
        assert d.county_id == "cty_king"
        assert d.channel == FilingChannel.NOTICE_TO_CREDITORS
        assert d.petitioner_name is not None
        assert d.attorney_name is not None

    # Pierce County (Tacoma Daily Index)
    pierce_dockets = LegalNoticesHarvester.harvest(county_id="cty_pierce", days_back=7)
    assert len(pierce_dockets) > 0
    assert any("Tacoma Daily Index" in (d.raw_snippet or "") for d in pierce_dockets)

def test_auditor_non_probate_harvester():
    # High-value non-probate real estate instruments (LOPA / TODD / CPA)
    non_probate = AuditorHarvester.harvest(county_id="cty_pierce", days_back=10)
    assert len(non_probate) > 0
    for d in non_probate:
        assert d.channel == FilingChannel.AUDITOR_NON_PROBATE
        assert d.instrument_number is not None
        assert d.property_hint is not None

def test_ingestion_pipeline_deduplication_and_commit():
    db = SessionLocal()
    try:
        unique_case_num = "TEST-INGEST-999-PR"
        # Ensure clean state for test
        existing = db.query(ProbateCaseModel).filter(ProbateCaseModel.case_number == unique_case_num).first()
        if existing:
            db.query(OpportunityModel).filter(OpportunityModel.case_id == existing.id).delete()
            db.delete(existing)
            db.commit()

        dockets = [
            ScrapedDocket(
                case_number=unique_case_num,
                decedent="Test Decedent Estate",
                county_id="cty_pierce",
                channel=FilingChannel.SUPERIOR_COURT_DOCKET,
                petitioner_name="Test Petitioner",
                petitioner_relationship="Surviving Spouse",
                attorney_name="Legal Test Counsel PS",
                property_hint="123 Test St, Tacoma, WA 98402"
            )
        ]

        # First run: should ingest 1 case and 1 opportunity
        summary1 = IngestionPipeline.process_dockets(db, dockets, operator_name="Test Runner")
        assert summary1.total_found == 1
        assert summary1.cases_ingested == 1
        assert summary1.opportunities_created == 1
        assert summary1.duplicates_skipped == 0

        # Second run with same docket: should skip as duplicate
        summary2 = IngestionPipeline.process_dockets(db, dockets, operator_name="Test Runner")
        assert summary2.total_found == 1
        assert summary2.cases_ingested == 0
        assert summary2.opportunities_created == 0
        assert summary2.duplicates_skipped == 1

        # Verify opportunity created at stage 'NEW'
        saved_case = db.query(ProbateCaseModel).filter(ProbateCaseModel.case_number == unique_case_num).first()
        assert saved_case is not None
        saved_opp = db.query(OpportunityModel).filter(OpportunityModel.case_id == saved_case.id).first()
        assert saved_opp is not None
        assert saved_opp.workflow_stage == "NEW"

    finally:
        # Cleanup test fixture
        case_to_clean = db.query(ProbateCaseModel).filter(ProbateCaseModel.case_number == unique_case_num).first()
        if case_to_clean:
            db.query(OpportunityModel).filter(OpportunityModel.case_id == case_to_clean.id).delete()
            db.delete(case_to_clean)
            db.commit()
        db.close()

def test_api_harvest_endpoint():
    headers = {
        "x-clerk-user-id": "operator_test",
        "x-clerk-role": "County Intelligence Lead"
    }

    # Harvest Pierce LINX
    res_linx = client.post(
        "/api/ingestion/harvest",
        json={"county_id": "cty_pierce", "channel": "SUPERIOR_COURT_DOCKET", "days_back": 3},
        headers=headers
    )
    # LINX Harvester returns [] per Rule §4
    assert res_linx.status_code == 200
    data = res_linx.json()
    assert "total_found" in data

    # Harvest Auditor Non-Probate (LOPA)
    res_lopa = client.post(
        "/api/ingestion/harvest",
        json={"county_id": "cty_thurston", "channel": "AUDITOR_NON_PROBATE", "days_back": 5},
        headers=headers
    )
    assert res_lopa.status_code == 200
    data_lopa = res_lopa.json()
    assert data_lopa["total_found"] > 0

def test_api_bulk_import_csv():
    headers = {
        "x-clerk-user-id": "operator_test",
        "x-clerk-role": "Clerk of Court Ingestion"
    }
    raw_csv = """26-4-CSV-001, Eleanor Vance Estate, Theo Vance, Hill House Law PLLC, 4500 Blackwood Dr
26-4-CSV-002, Arthur Hastings Estate, Mary Hastings, Poirot & Hastings LLP, 1200 Pacific Ave"""

    res = client.post(
        "/api/ingestion/bulk-import",
        json={
            "county_id": "cty_pierce",
            "channel": "SUPERIOR_COURT_DOCKET",
            "raw_text": raw_csv
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_found"] == 2
    assert (data["cases_ingested"] + data["duplicates_skipped"]) == 2

def test_api_channels_and_stats():
    # Test channels
    res_ch = client.get("/api/ingestion/channels")
    assert res_ch.status_code == 200
    channels = res_ch.json()
    assert len(channels) >= 5
    channel_types = [c["type"] for c in channels]
    assert "SUPERIOR_COURT_DOCKET" in channel_types
    assert "NOTICE_TO_CREDITORS" in channel_types
    assert "AUDITOR_NON_PROBATE" in channel_types

    # Test stats
    res_st = client.get("/api/ingestion/stats")
    assert res_st.status_code == 200
    stats = res_st.json()
    assert "total_cases_ingested" in stats
    assert "total_opportunities_created" in stats
    assert "non_probate_filings" in stats
    assert stats["automated_harvester_status"] == "ACTIVE_POLLING"

def test_harvesters_raise_when_demo_mode_disabled(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    from gieni_os.ingestion.models import HarvesterUnavailableError
    with pytest.raises(HarvesterUnavailableError):
        LinxHarvester.harvest()
    with pytest.raises(HarvesterUnavailableError):
        LegalNoticesHarvester.harvest("cty_king")
    with pytest.raises(HarvesterUnavailableError):
        AuditorHarvester.harvest("cty_pierce")
