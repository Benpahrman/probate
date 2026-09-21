"""
Test Suite for Recovery Runbooks & Reinforcement Learning Engine
"""

import pytest
from gieni_os.recovery.runbooks import (
    ScraperRecoveryRunbook,
    OCRRecoveryRunbook,
    TitleConflictRunbook,
    AuthorityAmbiguityRunbook,
    PartnerWebhookRecoveryRunbook
)
from gieni_os.learning.reinforcement import ReinforcementLearningEngine
from gieni_os.events.schemas import TelemetryIngestedEvent

def test_scraper_recovery_runbook_success():
    def mock_scraper(proxy):
        if "central" in proxy:
            return "OK"
        raise ConnectionError("Blocked")

    res = ScraperRecoveryRunbook.execute_with_recovery(mock_scraper, "https://court.wa.gov")
    assert res["status"] == "SUCCESS"
    assert res["proxy_used"] == "us-central-residential"
    assert res["attempts"] == 2

def test_scraper_recovery_exhaustion():
    def failing_scraper(proxy):
        raise ConnectionError("Down")

    with pytest.raises(RuntimeError):
        ScraperRecoveryRunbook.execute_with_recovery(failing_scraper, "https://court.wa.gov")

def test_ocr_and_title_runbooks():
    ocr_evt = OCRRecoveryRunbook.isolate_corrupted_document("c_1", "s3://bad.pdf", "Corrupted PDF")
    assert ocr_evt.exceptionCode == "EXC_OCR_CORRUPTION"
    assert ocr_evt.assignedQueue == "HITL_DOCUMENT_QUEUE"

    title_evt = TitleConflictRunbook.isolate_title_exception("c_2", "p_2", "Deed cloud")
    assert title_evt.exceptionCode == "EXC_TITLE_CLOUD"
    assert title_evt.assignedQueue == "TITLE_CURATIVE_QUEUE"

    auth_evt = AuthorityAmbiguityRunbook.isolate_authority_exception("c_3", "Will contest")
    assert auth_evt.exceptionCode == "EXC_AUTHORITY_AMBIGUITY"

    webhook_res = PartnerWebhookRecoveryRunbook.handle_failed_webhook("cli_1", {"data": "test"})
    assert webhook_res["action"] == "DLQ_FALLBACK_SMS"

def test_reinforcement_learning_engine():
    engine = ReinforcementLearningEngine()
    engine.ingest_telemetry_event(
        TelemetryIngestedEvent("opp_1", "cli_1", "CLOSED_WON", "Closed", True, 30000.0)
    )
    engine.ingest_telemetry_event(
        TelemetryIngestedEvent("opp_2", "cli_1", "CLOSED_LOST", "Lost", False, 0.0)
    )

    recal = engine.recalibrate("53053")
    assert recal["sample_size"] == 2
    assert recal["closed_won_count"] == 1
    assert recal["calibrated_county_friction_coefficient"] < 1.0
    assert "equity_spread" in recal["updated_feature_weights"]
