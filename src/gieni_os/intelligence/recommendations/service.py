"""
Gieni OS Recommendation Service (Subsystem 6)
Synthesizes verified statutory rules, authority states, and control archetypes
to generate prescriptive next actions for Researchers, QC Analysts, and Investor Clients.
"""

from typing import List, Dict, Any, Optional
from gieni_os.intelligence.models import (
    StakeholderRole,
    RecommendationActionDTO,
)


class RecommendationService:
    """Prescriptive operational guidance engine."""

    def next_action(
        self,
        context: Dict[str, Any],
        role: StakeholderRole = StakeholderRole.RESEARCHER,
    ) -> List[RecommendationActionDTO]:
        """Generate targeted next steps tailored to stakeholder role."""
        actions: List[RecommendationActionDTO] = []

        auth_profile = context.get("authority_profile", {})
        own_profile = context.get("ownership_profile", {})
        ctrl_profile = context.get("control_profile", {})
        opp_profile = context.get("opportunity_profile", {})

        auth_tier = auth_profile.get("authority_tier", "TIER_1_UNCONTESTED_NONINTERVENTION")
        can_sign = auth_profile.get("can_execute_psa", True)
        fiduciary = ctrl_profile.get("primary_decision_maker", "Personal Representative")
        equity = own_profile.get("net_distributable_equity", 0)

        # 1. Researcher Actions
        if role == StakeholderRole.RESEARCHER:
            if not can_sign or "UNRESOLVED" in str(auth_tier):
                actions.append(
                    RecommendationActionDTO(
                        action_type="SEARCH_DOCKET",
                        title="Audit Odyssey / LINX for Letters Issuance",
                        instructions="Inspect superior court docket for pending Petition for Nonintervention Powers or creditor notice filings.",
                        urgency="HIGH",
                        target_role=role,
                        statutory_citations=["RCW 11.68.011", "RCW 11.28.110"],
                    )
                )
            else:
                actions.append(
                    RecommendationActionDTO(
                        action_type="SKIP_TRACE_PR",
                        title=f"Obtain Direct Contact for {fiduciary}",
                        instructions="Execute Tier-1 mobile skip-trace across municipal records, deed grantors, and utility filings.",
                        urgency="MEDIUM",
                        target_role=role,
                        statutory_citations=["RCW 11.68.011"],
                    )
                )

        # 2. QC Analyst Actions
        elif role == StakeholderRole.QC_ANALYST:
            if equity < 50000:
                actions.append(
                    RecommendationActionDTO(
                        action_type="ESCALATE_QC",
                        title="Equity Margin Alert (< $50,000 Cushion)",
                        instructions="Verify senior mortgages, tax liens, and Medicaid estate recovery claims before stamping for client dispatch.",
                        urgency="CRITICAL",
                        target_role=role,
                        statutory_citations=["RCW 43.20B.080 (Medicaid Recovery)"],
                    )
                )
            else:
                actions.append(
                    RecommendationActionDTO(
                        action_type="STAMP_APPROVAL",
                        title="Certify 6-Gate Statutory Compliance",
                        instructions="All statutory gates verified. Stamp Packet of Facts for automated client delivery.",
                        urgency="LOW",
                        target_role=role,
                        statutory_citations=["QC-6-GATE-SPEC"],
                    )
                )

        # 3. Investor Client Actions
        elif role == StakeholderRole.CLIENT_INVESTOR:
            if can_sign:
                actions.append(
                    RecommendationActionDTO(
                        action_type="SUBMIT_CASH_PSA",
                        title="Direct Purchase & Sale Agreement Submission",
                        instructions=f"PR possesses autonomous nonintervention power of sale. Submit cash convenience offer to {fiduciary}.",
                        urgency="HIGH",
                        target_role=role,
                        statutory_citations=["RCW 11.68.011"],
                    )
                )
            else:
                actions.append(
                    RecommendationActionDTO(
                        action_type="MONITOR_HEARING",
                        title="Wait for Superior Court Hearing",
                        instructions="Order granting nonintervention powers pending court calendar. Monitor case docket before signing binding agreement.",
                        urgency="MEDIUM",
                        target_role=role,
                        statutory_citations=["RCW 11.28.120"],
                    )
                )

        # 4. Fallback / Platform Admin
        else:
            actions.append(
                RecommendationActionDTO(
                    action_type="MONITOR_PIPELINE",
                    title="System Lifecycle Verification",
                    instructions="Monitor opportunity velocity through the 6-stage lifecycle pipeline.",
                    urgency="LOW",
                    target_role=role,
                    statutory_citations=["GIENI-OS-SPEC"],
                )
            )

        return actions
