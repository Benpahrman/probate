"""
County Validator Engine (Phase 7: Test 1 - 100 Probate Case Challenge)
Validates county intake accuracy, Property Alignment Score (PAS >= 70),
and categorizes failure modes into actionable backlog items.
"""

from typing import List, Dict, Any, Optional
import time
from gieni_os.domain.property import SitusAddress, PropertyRecord
from gieni_os.engines.property_engine import PropertyEngine
from gieni_os.validation.models import (
    CountyValidationReport,
    FailureCategory
)

class CountyValidator:
    """
    Executes Test 1: 100 Probate Case Challenge for a designated county
    (default: Thurston County, WA).
    """

    DEFAULT_COUNTY_ID = "thurston"
    DEFAULT_COUNTY_NAME = "Thurston County, WA"

    @classmethod
    def generate_thurston_100_cases(cls) -> List[Dict[str, Any]]:
        """
        Generates 100 realistic Thurston County probate filings modeling
        empirical county court docket patterns and real-world failure distributions:
        - ~4% unparsable / incomplete docket filings
        - ~4% missing real property (estate consists of personal property/vehicles/cash only)
        - ~3% bad situs address (e.g., PO Box without parcel situs)
        - ~2% multiple APNs (unsegregated timber/rural acreage)
        - ~2% trust ownership (property deeded into irrevocable trust prior to death)
        - ~2% broken title / unprobated prior deceased co-owner
        - Remaining ~83% valid properties with PAS >= 70
        """
        # In compliance with Rule §4: Zero Synthetic Entities
        # We no longer generate fake records or fictional names.
        return []

    @classmethod
    def run_100_case_challenge(
        cls,
        cases: Optional[List[Dict[str, Any]]] = None,
        county_id: str = DEFAULT_COUNTY_ID,
        county_name: str = DEFAULT_COUNTY_NAME
    ) -> CountyValidationReport:
        """
        Executes Test 1 against 100 cases and calculates metrics:
        - Intake Accuracy: >= 95% parsed correctly
        - Property Match: PAS >= 70 (target 90%, min 80%)
        - Failure Tracking into backlog action items
        """
        if cases is None:
            cases = cls.generate_thurston_100_cases()

        total_cases = len(cases)
        parsed_count = 0
        property_matches = 0
        pas_above_70 = 0
        failure_breakdown: Dict[str, int] = {
            FailureCategory.MISSING_PROPERTY.value: 0,
            FailureCategory.BAD_ADDRESS.value: 0,
            FailureCategory.MULTIPLE_APNS.value: 0,
            FailureCategory.TRUST_OWNERSHIP.value: 0,
            FailureCategory.BROKEN_TITLE.value: 0,
            FailureCategory.CONTESTED_PETITION.value: 0,
            FailureCategory.DECEASED_FIDUCIARY.value: 0,
            FailureCategory.OTHER.value: 0
        }

        for case in cases:
            # 1. Intake Parsing check
            decedent = case.get("decedent_name", "").strip()
            petition = case.get("petition_type", "").strip()
            case_number = case.get("case_number", "").strip()

            if not decedent or not petition or not case_number or case.get("failure_tag") == "PARSE_ERROR":
                failure_breakdown[FailureCategory.OTHER.value] += 1
                continue

            parsed_count += 1

            # 2. Property Matching & Alignment Score
            raw_address = case.get("raw_address", "").strip()
            has_real_estate = case.get("has_real_estate", True)
            candidate_apn = case.get("candidate_apn")
            is_trust_owned = case.get("is_trust_owned", False)
            is_broken_title = case.get("is_broken_title", False)
            multiple_apns = case.get("multiple_apns", False)

            if not has_real_estate or not raw_address:
                failure_breakdown[FailureCategory.MISSING_PROPERTY.value] += 1
                continue

            if "PO BOX" in raw_address.upper() or "P.O. BOX" in raw_address.upper() or len(raw_address.split(",")) < 2:
                failure_breakdown[FailureCategory.BAD_ADDRESS.value] += 1
                continue

            if multiple_apns:
                failure_breakdown[FailureCategory.MULTIPLE_APNS.value] += 1
                continue

            if is_trust_owned:
                failure_breakdown[FailureCategory.TRUST_OWNERSHIP.value] += 1
                continue

            if is_broken_title:
                failure_breakdown[FailureCategory.BROKEN_TITLE.value] += 1
                continue

            # Standard property reconciliation using PropertyEngine
            prop_record = PropertyEngine.reconcile_parcel(
                raw_address=raw_address,
                county_id=county_id,
                decedent_name=decedent,
                candidate_apn=candidate_apn
            )

            property_matches += 1
            if prop_record.pas_score >= PropertyEngine.PAS_THRESHOLD:
                pas_above_70 += 1

        intake_accuracy = round((parsed_count / total_cases) * 100.0, 1) if total_cases > 0 else 0.0
        property_match_pct = round((pas_above_70 / total_cases) * 100.0, 1) if total_cases > 0 else 0.0

        # Formulate engineering backlog items from failure modes
        backlog_items: List[str] = []
        if failure_breakdown[FailureCategory.BAD_ADDRESS.value] > 0:
            backlog_items.append(
                f"Backlog #1: Implement Thurston County Assessor owner-index reverse lookup for PO Box addresses ({failure_breakdown[FailureCategory.BAD_ADDRESS.value]} cases)."
            )
        if failure_breakdown[FailureCategory.MISSING_PROPERTY.value] > 0:
            backlog_items.append(
                f"Backlog #2: Add docket estate asset filter to auto-flag personal-property-only probates prior to property ingestion ({failure_breakdown[FailureCategory.MISSING_PROPERTY.value]} cases)."
            )
        if failure_breakdown[FailureCategory.MULTIPLE_APNS.value] > 0:
            backlog_items.append(
                f"Backlog #3: Build multi-APN parcel clustering algorithm for unsegregated rural/timber acreage ({failure_breakdown[FailureCategory.MULTIPLE_APNS.value]} cases)."
            )
        if failure_breakdown[FailureCategory.TRUST_OWNERSHIP.value] > 0:
            backlog_items.append(
                f"Backlog #4: Integrate certificate of trust parser to identify successor trustees for trust-titled real property ({failure_breakdown[FailureCategory.TRUST_OWNERSHIP.value]} cases)."
            )
        if failure_breakdown[FailureCategory.BROKEN_TITLE.value] > 0:
            backlog_items.append(
                f"Backlog #5: Create prior unprobated co-owner chain-of-title exception workflow ({failure_breakdown[FailureCategory.BROKEN_TITLE.value]} cases)."
            )

        return CountyValidationReport(
            county_id=county_id,
            county_name=county_name,
            total_cases_entered=total_cases,
            cases_parsed_successfully=parsed_count,
            intake_accuracy_pct=intake_accuracy,
            property_matches_found=property_matches,
            pas_above_70_count=pas_above_70,
            property_match_pct=property_match_pct,
            failure_breakdown=failure_breakdown,
            backlog_action_items=backlog_items,
            generated_at=time.time()
        )

    @classmethod
    def generate_markdown_report(cls, report: CountyValidationReport) -> str:
        """Renders the official County Validation Report deliverable in Markdown."""
        lines = [
            f"# County Validation Report: {report.county_name}",
            f"**Validation Run Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.generated_at))}",
            f"**Target County:** {report.county_name} (`{report.county_id}`)",
            "",
            "## Executive Summary",
            f"- **Total Cases Entered:** {report.total_cases_entered}",
            f"- **Parsed Correctly:** {report.cases_parsed_successfully} / {report.total_cases_entered} ({report.intake_accuracy_pct}% vs Target $\\ge 95\\%$)",
            f"- **Property Matches with PAS $\\ge 70$:** {report.pas_above_70_count} / {report.total_cases_entered} ({report.property_match_pct}% vs Minimum $80\\%$, Target $90\\%$)",
            f"- **Validation Status:** {'PASSED' if report.intake_accuracy_pct >= 95.0 and report.property_match_pct >= 80.0 else 'RECALIBRATION_REQUIRED'}",
            "",
            "## Failure Mode Breakdown",
            "| Failure Category | Occurrences | Impact Description |",
            "| :--- | :--- | :--- |"
        ]

        impact_map = {
            FailureCategory.MISSING_PROPERTY.value: "Probate filing does not contain real estate (personal property only).",
            FailureCategory.BAD_ADDRESS.value: "Situs address was a PO Box or malformed without physical parcel locator.",
            FailureCategory.MULTIPLE_APNS.value: "Multiple conflicting unsegregated parcels attached to single estate.",
            FailureCategory.TRUST_OWNERSHIP.value: "Real property held in living/irrevocable trust prior to decedent death.",
            FailureCategory.BROKEN_TITLE.value: "Unprobated predeceased joint tenant or broken chain-of-title.",
            FailureCategory.CONTESTED_PETITION.value: "Contested will or competing petitions for administration.",
            FailureCategory.DECEASED_FIDUCIARY.value: "Named fiduciary predeceased the decedent without successor nominated.",
            FailureCategory.OTHER.value: "Court docket OCR/PDF parse failure or missing core case metadata."
        }

        for cat, count in report.failure_breakdown.items():
            if count > 0:
                desc = impact_map.get(cat, "Unclassified failure")
                lines.append(f"| `{cat}` | **{count}** | {desc} |")

        lines.extend([
            "",
            "## Engineering Backlog Items",
            "These items translate empirical court failure modes directly into prioritized engineering tasks:"
        ])

        for item in report.backlog_action_items:
            lines.append(f"- {item}")

        return "\n".join(lines)
