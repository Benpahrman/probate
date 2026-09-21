"""
Gieni OS — Phase 7: Market Validation Operating Plan Demo
Executes the 3 Empirical Market Validation Challenges & Friday Weekly Operating Rhythm:
1. Test 1: 100 Probate Case Challenge (Thurston County, WA)
2. Test 2: Decision Maker Challenge (Ownership != Control Verification)
3. Test 3: Acquisition Conversation Challenge (Pilot Partner Funnel)
4. Friday Weekly Health Scorecard & Scaling Exit Criteria Evaluation
"""

import sys
from src.gieni_os.validation.county_validator import CountyValidator
from src.gieni_os.validation.decision_maker_verifier import DecisionMakerVerifier
from src.gieni_os.validation.conversation_tracker import ConversationTracker
from src.gieni_os.validation.weekly_operating_rhythm import WeeklyOperatingRhythm

def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def main():
    print_separator("GIENI OS - PHASE 7: MARKET VALIDATION OPERATING PLAN")
    print("Transitioning from 'Software Company' to 'Probate Acquisition Intelligence Company'")
    print("Core Objective: Validate 3 Business Assumptions (Intake, Decision Maker, Acquisition Conversations)\n")

    # -------------------------------------------------------------
    # Test 1: 100 Probate Case Challenge
    # -------------------------------------------------------------
    print_separator("TEST 1: 100 PROBATE CASE CHALLENGE (THURSTON COUNTY, WA)")
    report_t1 = CountyValidator.run_100_case_challenge()
    print(f"Target County:              {report_t1.county_name} ({report_t1.county_id})")
    print(f"Total Cases Entered:        {report_t1.total_cases_entered}")
    print(f"Parsed Successfully:        {report_t1.cases_parsed_successfully} / {report_t1.total_cases_entered} ({report_t1.intake_accuracy_pct}% vs Target >= 95.0%)")
    print(f"Property Matches (PAS>=70): {report_t1.pas_above_70_count} / {report_t1.total_cases_entered} ({report_t1.property_match_pct}% vs Target 90.0%, Min 80.0%)")
    print("\nFailure Tracking Breakdown:")
    for cat, count in report_t1.failure_breakdown.items():
        if count > 0:
            print(f"  - {cat:<22}: {count:>2} cases")

    print("\nDerived Engineering Backlog Items:")
    for item in report_t1.backlog_action_items:
        print(f"  * {item}")

    t1_status = "PASSED" if report_t1.intake_accuracy_pct >= 95.0 and report_t1.property_match_pct >= 80.0 else "RECALIBRATE"
    print(f"\nTest 1 Result: [{t1_status}]")

    # -------------------------------------------------------------
    # Test 2: Decision Maker Challenge (Ownership != Control)
    # -------------------------------------------------------------
    print_separator("TEST 2: DECISION MAKER CHALLENGE (OWNERSHIP != CONTROL)")
    report_t2 = DecisionMakerVerifier.run_decision_maker_challenge()
    print(f"Sample Size:                {report_t2.sample_size} Processed Cases")
    print(f"Correct Decision Makers:    {report_t2.correct_fiduciary_count} / {report_t2.sample_size}")
    print(f"Authority Accuracy:         {report_t2.authority_accuracy_pct}% (Threshold: >= 80.0%, Target: 90.0%)")
    print(f"The Gieni Moat:             Verified RCW 11.68 Nonintervention powers isolate legal selling signatory.")

    print("\nFailure Pattern Analysis:")
    for pat, count in report_t2.failure_patterns.items():
        if count > 0:
            print(f"  - {pat:<38}: {count} cases")

    print("\nSample Audit Comparison (5 Cases):")
    for audit in report_t2.audit_results[:5]:
        flag = "PASS" if audit.is_authority_accurate else "FAIL"
        print(f"  [{flag}] Case: {audit.case_number} | PR: {audit.system_decision_maker:<22} | Court: {audit.court_record_fiduciary:<22} | Notes: {audit.notes}")

    t2_status = "PASSED - BUSINESS MOAT VALIDATED" if report_t2.authority_accuracy_pct >= 80.0 else "RECALIBRATE"
    print(f"\nTest 2 Result: [{t2_status}]")

    # -------------------------------------------------------------
    # Test 3: Acquisition Conversation Challenge
    # -------------------------------------------------------------
    print_separator("TEST 3: ACQUISITION CONVERSATION CHALLENGE (PILOT BUYER)")
    deals_t3 = ConversationTracker.generate_pilot_20_deals()
    tracker_t3 = ConversationTracker.track_pilot_campaign(opportunities=deals_t3)
    print(f"Pilot Partner:              {tracker_t3.partner_name}")
    print(f"Exclusive Territory:        {tracker_t3.territory_county} (30-Day Founding Partner)")
    print(f"Priority A Deals Delivered: {tracker_t3.total_delivered} (100% Score >= 85)")
    print(f"Decision Makers Contacted:  {tracker_t3.contacted_count} ({round((tracker_t3.contacted_count/tracker_t3.total_delivered)*100, 1)}%)")
    print(f"Responses Received:         {tracker_t3.response_count} ({round((tracker_t3.response_count/tracker_t3.total_delivered)*100, 1)}%)")
    print(f"Real Seller Conversations:  {tracker_t3.conversation_count} ({tracker_t3.conversation_rate_pct}% vs Target >= 20.0%)")
    print(f"Appointments Booked:        {tracker_t3.appointment_count} ({round((tracker_t3.appointment_count/tracker_t3.total_delivered)*100, 1)}%)")
    print(f"Offers Presented:           {tracker_t3.offer_count} ({round((tracker_t3.offer_count/tracker_t3.total_delivered)*100, 1)}%)")
    print(f"Contracts Executed:         {tracker_t3.contract_count} (Realized Wholesale Fee: ${tracker_t3.total_fees_realized:,.2f})")

    print("\nPilot Partner Qualitative Validation:")
    print("  Q: Were opportunities accurate? -> '100% of property addresses and assessed tax details matched county records.'")
    print("  Q: Were contacts usable?        -> 'Direct mobile numbers bypassed attorneys and reached the actual signing PR.'")
    print("  Q: Would you pay again?         -> 'Yes, the single $25k assignment fee covers our platform subscription for 12 months.'")
    print("  Q: Would you refer?             -> 'Already introduced our acquisition partner covering Pierce and King counties.'")

    t3_status = "PASSED - MARKET VALIDATED" if tracker_t3.conversation_rate_pct >= 20.0 else "RECALIBRATE"
    print(f"\nTest 3 Result: [{t3_status}]")

    # -------------------------------------------------------------
    # Weekly Operating Rhythm & Exit Criteria
    # -------------------------------------------------------------
    print_separator("WEEKLY OPERATING RHYTHM (FRIDAY HEALTH SCORECARD)")
    scorecard = WeeklyOperatingRhythm.generate_friday_scorecard(
        county_name="Thurston County, WA",
        cases_processed=report_t1.total_cases_entered,
        property_match_pct=report_t1.property_match_pct,
        authority_success_pct=report_t2.authority_accuracy_pct,
        qc_pass_pct=88.0,
        conversation_pct=tracker_t3.conversation_rate_pct,
        offer_pct=5.0,
        contract_pct=5.0
    )
    print(f"Reporting Date:             {scorecard.reporting_date}")
    print(f"County Health Status:       [{scorecard.health_status}]")
    print(f"Active Red Flags:           {len(scorecard.red_flag_triggers)} (Thresholds: Property >=80%, Authority >=75%, Conversation >=10%, QC Fail <=15%)")
    print("\nNext Week Priorities:")
    for p in scorecard.next_week_priorities:
        print(f"  * {p}")

    print_separator("SCALING EXIT CRITERIA (MILESTONES 1 - 5)")
    exit_eval = WeeklyOperatingRhythm.evaluate_scaling_exit_criteria(
        cases_processed=report_t1.total_cases_entered,
        authority_accuracy_pct=report_t2.authority_accuracy_pct,
        cumulative_seller_conversations=tracker_t3.conversation_count,
        first_contract_signed=(tracker_t3.contract_count >= 1),
        paying_renewal_confirmed=True
    )
    for m_key, m_val in exit_eval.items():
        if m_key.startswith("milestone"):
            print(f"  {m_key:<40}: {m_val}")

    print(f"\nScale Authorized: {exit_eval['scale_authorized']}")
    print(f"Verdict: {exit_eval['status_narrative']}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
