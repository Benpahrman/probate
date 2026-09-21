"""
Unit & Integration Tests for Phase 7: Market Validation Operating Plan
Validates:
1. Test 1: 100 Probate Case Challenge (CountyValidator)
2. Test 2: Decision Maker Challenge (DecisionMakerVerifier)
3. Test 3: Acquisition Conversation Challenge (ConversationTracker)
4. Friday Weekly Operating Rhythm & Red Flag Triggers (WeeklyOperatingRhythm)
"""

import pytest
from gieni_os.validation.models import (
    FailureCategory,
    CountyValidationReport,
    DecisionMakerChallengeReport,
    PilotConversationTracker,
    WeeklyHealthScorecard
)
from gieni_os.validation.county_validator import CountyValidator
from gieni_os.validation.decision_maker_verifier import DecisionMakerVerifier
from gieni_os.validation.conversation_tracker import ConversationTracker
from gieni_os.validation.weekly_operating_rhythm import WeeklyOperatingRhythm


class TestPhase7MarketValidation:
    """Test suite for Phase 7 Market Validation challenges and weekly rhythm."""

    # ---------------------------------------------------------
    # Test 1: 100 Probate Case Challenge
    # ---------------------------------------------------------
    @pytest.mark.skip(reason="Synthetic data generation removed per Rule §4")
    def test_county_validator_generate_cases(self):
        cases = CountyValidator.generate_thurston_100_cases()
        assert len(cases) == 100
        # Check that we have Thurston County filings
        assert all(c["county_id"] == "thurston" for c in cases)
        # Check that failure categories are represented
        failure_tags = [c.get("failure_tag") for c in cases if c.get("failure_tag")]
        assert "PARSE_ERROR" in failure_tags
        assert FailureCategory.MISSING_PROPERTY.value in failure_tags
        assert FailureCategory.BAD_ADDRESS.value in failure_tags
        assert FailureCategory.MULTIPLE_APNS.value in failure_tags
        assert FailureCategory.TRUST_OWNERSHIP.value in failure_tags
        assert FailureCategory.BROKEN_TITLE.value in failure_tags

    @pytest.mark.skip(reason="Synthetic data generation removed per Rule §4")
    def test_county_validator_100_case_challenge_metrics(self):
        report = CountyValidator.run_100_case_challenge()
        assert isinstance(report, CountyValidationReport)
        assert report.total_cases_entered == 100
        # Target: >= 95% parsed correctly
        assert report.intake_accuracy_pct >= 95.0
        # Target: PAS >= 70 in >= 80% of cases
        assert report.property_match_pct >= 80.0
        assert report.pas_above_70_count >= 80

        # Check failure breakdown
        assert report.failure_breakdown[FailureCategory.MISSING_PROPERTY.value] > 0
        assert report.failure_breakdown[FailureCategory.BAD_ADDRESS.value] > 0
        assert report.failure_breakdown[FailureCategory.MULTIPLE_APNS.value] > 0
        assert report.failure_breakdown[FailureCategory.TRUST_OWNERSHIP.value] > 0
        assert report.failure_breakdown[FailureCategory.BROKEN_TITLE.value] > 0

        # Backlog items created
        assert len(report.backlog_action_items) >= 4
        assert any("PO Box" in item for item in report.backlog_action_items)

        # Markdown report generation
        md = CountyValidator.generate_markdown_report(report)
        assert "# County Validation Report: Thurston County, WA" in md
        assert "Executive Summary" in md
        assert "Engineering Backlog Items" in md

    # ---------------------------------------------------------
    # Test 2: Decision Maker Challenge (Ownership != Control)
    # ---------------------------------------------------------
    @pytest.mark.skip(reason="Synthetic data generation removed per Rule §4")
    def test_decision_maker_verifier_50_cases(self):
        cases = DecisionMakerVerifier.generate_50_ground_truth_cases()
        assert len(cases) == 50
        assert any(c.get("edge_case") == "CO_FIDUCIARY_JOINT_SIGNATURE_REQUIRED" for c in cases)
        assert any(c.get("edge_case") == "SUCCESSOR_PR_SUBSTITUTION" for c in cases)
        assert any(c.get("edge_case") == "CONTESTED_PETITION_FROZEN_AUTHORITY" for c in cases)

    @pytest.mark.skip(reason="Synthetic data generation removed per Rule §4")
    def test_decision_maker_challenge_accuracy(self):
        report = DecisionMakerVerifier.run_decision_maker_challenge()
        assert isinstance(report, DecisionMakerChallengeReport)
        assert report.sample_size == 50
        # Success Metric: >= 80% Authority Accuracy (Target: 90%)
        assert report.authority_accuracy_pct >= 80.0
        assert report.correct_fiduciary_count >= 40

        # Verify failure pattern categorization
        assert report.failure_patterns["CO_FIDUCIARY_JOINT_SIGNATURE_REQUIRED"] > 0
        assert report.failure_patterns["SUCCESSOR_PR_SUBSTITUTION"] > 0

        # Verify audit records detail
        assert len(report.audit_results) == 50
        first_audit = report.audit_results[0]
        assert first_audit.is_authority_accurate is True
        assert first_audit.system_authority_tier == "Tier 1: Court Certified"
        assert first_audit.court_letters_status == "LETTERS_TESTAMENTARY"

        # Markdown report generation
        md = DecisionMakerVerifier.generate_markdown_report(report)
        assert "# Decision Maker Challenge Report" in md
        assert "Ownership" in md and "Control" in md
        assert "Failure Pattern Analysis" in md

    # ---------------------------------------------------------
    # Test 3: Acquisition Conversation Challenge
    # ---------------------------------------------------------
    def test_conversation_tracker_pilot_campaign(self):
        deals = ConversationTracker.generate_pilot_20_deals()
        assert len(deals) == 20
        # All deals are Priority A
        assert all(d.priority_tier == "PRIORITY_A" for d in deals)
        assert all(d.composite_score >= 85 for d in deals)

        tracker = ConversationTracker.track_pilot_campaign(
            partner_name="Cascade Capital Acquisitions LLC",
            territory_county="Thurston County, WA",
            opportunities=deals
        )
        assert isinstance(tracker, PilotConversationTracker)
        assert tracker.total_delivered == 20
        assert tracker.contacted_count == 18
        assert tracker.response_count == 9
        assert tracker.conversation_count == 5
        # Target: Conversation Rate >= 20.0%
        assert tracker.conversation_rate_pct >= 20.0
        assert tracker.conversation_rate_pct == 25.0
        assert tracker.appointment_count == 2
        assert tracker.offer_count == 1
        assert tracker.contract_count == 1
        assert tracker.total_fees_realized == 25000.0

        # Markdown report generation
        md = ConversationTracker.generate_markdown_report(tracker)
        assert "# Acquisition Conversation Challenge Report" in md
        assert "Cascade Capital Acquisitions LLC" in md
        assert "Founding Pilot Partner Qualitative Feedback" in md
        assert "Would you pay again?" in md
        assert "$25,000.00" in md

    # ---------------------------------------------------------
    # Weekly Operating Rhythm & Red Flag Triggers
    # ---------------------------------------------------------
    def test_weekly_operating_rhythm_healthy(self):
        scorecard = WeeklyOperatingRhythm.generate_friday_scorecard(
            county_name="Thurston County, WA",
            cases_processed=100,
            property_match_pct=86.0,
            authority_success_pct=86.0,
            qc_pass_pct=88.0,
            conversation_pct=25.0,
            offer_pct=5.0,
            contract_pct=5.0
        )
        assert scorecard.health_status == "HEALTHY"
        assert len(scorecard.red_flag_triggers) == 0
        assert len(scorecard.next_week_priorities) >= 2

        md = WeeklyOperatingRhythm.generate_markdown_scorecard(scorecard)
        assert "# Friday Weekly Health Scorecard: Thurston County, WA" in md
        assert "Zero active red flags" in md

    def test_weekly_operating_rhythm_red_flags(self):
        # Trigger all 4 red flags:
        # 1. Property match < 80% (e.g. 74.0%)
        # 2. Authority accuracy < 75% (e.g. 70.0%)
        # 3. Conversation rate < 10% (e.g. 8.0%)
        # 4. QC failure > 15% (e.g. qc pass = 80.0% -> failure = 20%)
        scorecard = WeeklyOperatingRhythm.generate_friday_scorecard(
            county_name="Thurston County, WA",
            cases_processed=100,
            property_match_pct=74.0,
            authority_success_pct=70.0,
            qc_pass_pct=80.0,
            conversation_pct=8.0,
            offer_pct=1.0,
            contract_pct=0.0
        )
        assert scorecard.health_status == "CRITICAL_SYSTEM_RECALIBRATION"
        assert len(scorecard.red_flag_triggers) == 4
        assert any("Property Match" in rf for rf in scorecard.red_flag_triggers)
        assert any("Authority Accuracy" in rf for rf in scorecard.red_flag_triggers)
        assert any("Conversation Rate" in rf for rf in scorecard.red_flag_triggers)
        assert any("QC Failures" in rf for rf in scorecard.red_flag_triggers)

        md = WeeklyOperatingRhythm.generate_markdown_scorecard(scorecard)
        assert "Active Red Flag Triggers" in md

    def test_scaling_exit_criteria_evaluation(self):
        # Incomplete milestones
        res_incomplete = WeeklyOperatingRhythm.evaluate_scaling_exit_criteria(
            cases_processed=50,
            authority_accuracy_pct=75.0,
            cumulative_seller_conversations=8,
            first_contract_signed=False,
            paying_renewal_confirmed=False
        )
        assert res_incomplete["scale_authorized"] is False
        assert res_incomplete["milestone_1_100_cases_processed"]["passed"] is False

        # Complete milestones
        res_complete = WeeklyOperatingRhythm.evaluate_scaling_exit_criteria(
            cases_processed=100,
            authority_accuracy_pct=86.0,
            cumulative_seller_conversations=25,
            first_contract_signed=True,
            paying_renewal_confirmed=True
        )
        assert res_complete["scale_authorized"] is True
        assert res_complete["milestone_1_100_cases_processed"]["passed"] is True
        assert res_complete["milestone_2_80pct_authority_accuracy"]["passed"] is True
        assert res_complete["milestone_3_20_seller_conversations"]["passed"] is True
        assert res_complete["milestone_4_first_contract"]["passed"] is True
        assert res_complete["milestone_5_first_paying_renewal"]["passed"] is True
        assert "VALIDATED PROBATE ACQUISITION INTELLIGENCE BUSINESS" in res_complete["status_narrative"]
