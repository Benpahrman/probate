"""
Weekly Operating Rhythm Engine (Phase 7: Friday County Health Scorecard)
Evaluates weekly operating metrics, checks Red Flag Triggers, and tracks
the 5 Scaling Exit Criteria Milestones.
"""

from typing import List, Dict, Any, Optional
import time
from gieni_os.validation.models import WeeklyHealthScorecard

class WeeklyOperatingRhythm:
    """
    Automates the Friday Weekly Operating Rhythm for County Operations.
    """

    # Red Flag Thresholds
    RED_FLAG_PROPERTY_MATCH_MIN = 80.0
    RED_FLAG_AUTHORITY_ACCURACY_MIN = 75.0
    RED_FLAG_CONVERSATION_RATE_MIN = 10.0
    RED_FLAG_QC_FAILURE_MAX = 15.0  # i.e., QC Pass Rate must be >= 85.0%

    @classmethod
    def generate_friday_scorecard(
        cls,
        county_name: str = "Thurston County, WA",
        cases_processed: int = 100,
        property_match_pct: float = 86.0,
        authority_success_pct: float = 86.0,
        qc_pass_pct: float = 88.0,
        conversation_pct: float = 25.0,
        offer_pct: float = 5.0,
        contract_pct: float = 5.0,
        reporting_date: Optional[str] = None
    ) -> WeeklyHealthScorecard:
        """
        Calculates Friday County Health and tests Red Flag Triggers.
        """
        date_str = reporting_date or time.strftime("%Y-%m-%d (Friday)")
        red_flags: List[str] = []

        # 1. Property Match < 80%
        if property_match_pct < cls.RED_FLAG_PROPERTY_MATCH_MIN:
            red_flags.append(
                f"RED FLAG: Property Match ({property_match_pct}%) < {cls.RED_FLAG_PROPERTY_MATCH_MIN}%. Immediately investigate county assessor parcel feed & address normalizer."
            )

        # 2. Authority Accuracy < 75%
        if authority_success_pct < cls.RED_FLAG_AUTHORITY_ACCURACY_MIN:
            red_flags.append(
                f"RED FLAG: Authority Accuracy ({authority_success_pct}%) < {cls.RED_FLAG_AUTHORITY_ACCURACY_MIN}%. Immediately review RCW Title 11 Letters parsing logic."
            )

        # 3. Conversation Rate < 10%
        if conversation_pct < cls.RED_FLAG_CONVERSATION_RATE_MIN:
            red_flags.append(
                f"RED FLAG: Conversation Rate ({conversation_pct}%) < {cls.RED_FLAG_CONVERSATION_RATE_MIN}%. Immediately review contact phone quality & skip-tracing tiering."
            )

        # 4. QC Failures > 15% (QC Pass Rate < 85%)
        qc_failure_pct = round(100.0 - qc_pass_pct, 1)
        if qc_failure_pct > cls.RED_FLAG_QC_FAILURE_MAX:
            red_flags.append(
                f"RED FLAG: QC Failures ({qc_failure_pct}%) > {cls.RED_FLAG_QC_FAILURE_MAX}%. Immediately recalibrate Deal Friction Score (DFS) and equity thresholds."
            )

        # Determine overall health status
        if len(red_flags) == 0:
            health_status = "HEALTHY"
        elif any("Authority" in flag or "Conversation" in flag for flag in red_flags):
            health_status = "CRITICAL_SYSTEM_RECALIBRATION"
        else:
            health_status = "WARNING"

        # Determine priorities for next week
        priorities: List[str] = []
        if health_status != "HEALTHY":
            priorities.append("Priority 1: Resolve all active Red Flag investigation items.")
        else:
            priorities.append("Priority 1: Expand Thurston County pilot from 1 pilot partner to 2nd buyer cohort.")
            priorities.append("Priority 2: Prepare ingestion scraper for Pierce County (Tacoma).")
            priorities.append("Priority 3: Maintain >= 20% acquisition conversation rate with current lead flow.")

        return WeeklyHealthScorecard(
            reporting_date=date_str,
            county_name=county_name,
            cases_processed=cases_processed,
            property_match_pct=property_match_pct,
            authority_success_pct=authority_success_pct,
            qc_pass_pct=qc_pass_pct,
            conversation_pct=conversation_pct,
            offer_pct=offer_pct,
            contract_pct=contract_pct,
            red_flag_triggers=red_flags,
            health_status=health_status,
            next_week_priorities=priorities
        )

    @classmethod
    def evaluate_scaling_exit_criteria(
        cls,
        cases_processed: int,
        authority_accuracy_pct: float,
        cumulative_seller_conversations: int,
        first_contract_signed: bool,
        paying_renewal_confirmed: bool
    ) -> Dict[str, Any]:
        """
        Evaluates the 5 Scale Exit Criteria Milestones:
        - Milestone 1: 100 Cases Processed
        - Milestone 2: 80% Authority Accuracy
        - Milestone 3: 20+ Seller Conversations
        - Milestone 4: First Contract
        - Milestone 5: First Paying Renewal
        """
        m1 = cases_processed >= 100
        m2 = authority_accuracy_pct >= 80.0
        m3 = cumulative_seller_conversations >= 20
        m4 = first_contract_signed
        m5 = paying_renewal_confirmed

        scale_authorized = m1 and m2 and m3 and m4 and m5

        return {
            "milestone_1_100_cases_processed": {"passed": m1, "current": cases_processed, "target": 100},
            "milestone_2_80pct_authority_accuracy": {"passed": m2, "current": authority_accuracy_pct, "target": 80.0},
            "milestone_3_20_seller_conversations": {"passed": m3, "current": cumulative_seller_conversations, "target": 20},
            "milestone_4_first_contract": {"passed": m4, "status": "ACHIEVED" if m4 else "PENDING"},
            "milestone_5_first_paying_renewal": {"passed": m5, "status": "ACHIEVED" if m5 else "PENDING"},
            "scale_authorized": scale_authorized,
            "status_narrative": (
                "GIENI HAS OFFICIALLY CROSSED FROM SOFTWARE ARCHITECTURE TO VALIDATED PROBATE ACQUISITION INTELLIGENCE BUSINESS."
                if scale_authorized
                else "Active Phase 7 Market Validation underway. Satisfy all 5 milestones before multi-county scaling."
            )
        }

    @classmethod
    def generate_markdown_scorecard(cls, scorecard: WeeklyHealthScorecard) -> str:
        """Renders the Friday Weekly Health Scorecard in Markdown."""
        lines = [
            f"# Friday Weekly Health Scorecard: {scorecard.county_name}",
            f"**Reporting Date:** {scorecard.reporting_date}",
            f"**County Status:** `{scorecard.health_status}`",
            "",
            "## Weekly Operating Metrics",
            "| Metric | Result | Benchmark Target | Health Status |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Cases Processed** | **{scorecard.cases_processed}** | 100 Cases | {'OK' if scorecard.cases_processed >= 100 else 'UNDER'} |",
            f"| **Property Match Rate** | **{scorecard.property_match_pct}%** | $\\ge 80.0\\%$ | {'PASS' if scorecard.property_match_pct >= cls.RED_FLAG_PROPERTY_MATCH_MIN else 'FAIL'} |",
            f"| **Authority Success Rate** | **{scorecard.authority_success_pct}%** | $\\ge 75.0\\%$ (Target $90\\%$) | {'PASS' if scorecard.authority_success_pct >= cls.RED_FLAG_AUTHORITY_ACCURACY_MIN else 'FAIL'} |",
            f"| **QC Gate Pass Rate** | **{scorecard.qc_pass_pct}%** | $\\ge 85.0\\%$ (Fail $\\le 15\\%$) | {'PASS' if (100 - scorecard.qc_pass_pct) <= cls.RED_FLAG_QC_FAILURE_MAX else 'FAIL'} |",
            f"| **Conversation Rate** | **{scorecard.conversation_pct}%** | $\\ge 20.0\\%$ | {'PASS' if scorecard.conversation_pct >= 20.0 else ('WARNING' if scorecard.conversation_pct >= cls.RED_FLAG_CONVERSATION_RATE_MIN else 'FAIL')} |",
            f"| **Offer Rate** | **{scorecard.offer_pct}%** | $\\ge 5.0\\%$ | {'PASS' if scorecard.offer_pct >= 5.0 else 'TRACKING'} |",
            f"| **Contract Rate** | **{scorecard.contract_pct}%** | $\\ge 1.0\\%$ | {'PASS' if scorecard.contract_pct >= 1.0 else 'TRACKING'} |",
            ""
        ]

        if scorecard.red_flag_triggers:
            lines.extend([
                "## Active Red Flag Triggers",
                "> [!WARNING]",
                "> Immediate investigation required on the following operational anomalies:"
            ])
            for rf in scorecard.red_flag_triggers:
                lines.append(f"- {rf}")
            lines.append("")
        else:
            lines.extend([
                "## Red Flag Triggers",
                "> [!NOTE]",
                "> Zero active red flags. All operating thresholds within healthy operating limits.",
                ""
            ])

        lines.extend([
            "## Next Week Priorities",
            "Operating priorities derived from this week's scorecard:"
        ])
        for p in scorecard.next_week_priorities:
            lines.append(f"- {p}")

        return "\n".join(lines)
