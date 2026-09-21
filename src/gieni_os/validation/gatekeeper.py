"""
Gieni OS Six-Gate Quality Control Gatekeeper
Executes the Six Deterministic Quality Assurance Gates from Chapter 15.
A failure at any single gate intercepts the pipeline and halts delivery.

Transplanted from backend/app/services/gatekeeper.py.
Imports rewritten: app.engines.* → gieni_os.engines.*, app.models.enums → gieni_os.domain.enums
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field
from gieni_os.engines.pas import ParcelAttributionResult
from gieni_os.engines.equity import EquityWaterfallResult
from gieni_os.engines.scoring import OpportunityScoringResult
from gieni_os.domain.enums import AuthorityTier, PriorityTier


class GateCheckResult(BaseModel):
    gate_number: int = Field(..., ge=1, le=6)
    gate_name: str
    passed: bool
    failure_reason: Optional[str] = None
    telemetry_metadata: dict = Field(default_factory=dict)


class QualityControlAuditSummary(BaseModel):
    is_fully_certified: bool
    failed_gate: Optional[int] = None
    gate_results: List[GateCheckResult]
    disqualification_reason: Optional[str] = None


class QualityControlGatekeeper:
    """Executes the Six Deterministic Quality Assurance Gates from Chapter 15.
    A failure at any single gate intercepts the pipeline and halts delivery.
    """

    @staticmethod
    def verify_gate_1_docket_integrity(
        case_number: str,
        filing_date_valid: bool,
        petition_pdf_sha256: Optional[str]
    ) -> GateCheckResult:
        """Gate 1: Docket & Record Integrity Verification.
        Validates case regex, lookback window, and immutable SHA-256 petition artifact.
        """
        # Case number regex validation (standard alphanumeric docket with hyphen/slash format)
        case_regex = r"^[A-Za-z0-9\-/\.\s]{4,40}$"
        has_valid_format = bool(re.match(case_regex, case_number.strip()))

        if not has_valid_format:
            return GateCheckResult(
                gate_number=1,
                gate_name="Docket & Record Integrity",
                passed=False,
                failure_reason=f"Case number '{case_number}' violates county docket regex formatting."
            )

        if not filing_date_valid:
            return GateCheckResult(
                gate_number=1,
                gate_name="Docket & Record Integrity",
                passed=False,
                failure_reason="Filing date falls outside the valid municipal intake lookback window."
            )

        if not petition_pdf_sha256 or len(petition_pdf_sha256) != 64:
            return GateCheckResult(
                gate_number=1,
                gate_name="Docket & Record Integrity",
                passed=False,
                failure_reason="Missing or corrupt court petition PDF SHA-256 cryptographic digest."
            )

        return GateCheckResult(
            gate_number=1,
            gate_name="Docket & Record Integrity",
            passed=True,
            telemetry_metadata={"sha256": petition_pdf_sha256}
        )

    @staticmethod
    def verify_gate_2_parcel_attribution(pas_result: ParcelAttributionResult) -> GateCheckResult:
        """Gate 2: Parcel Attribution & Title Reconciliation.
        Enforces PAS >= 70.0 match threshold against county tax rolls.
        """
        if not pas_result.gate_2_passed:
            return GateCheckResult(
                gate_number=2,
                gate_name="Parcel Attribution & Title Reconciliation",
                passed=False,
                failure_reason=f"Parcel Attribution Score ({pas_result.pas_score}) is below the required 70.0 threshold.",
                telemetry_metadata={"pas_score": pas_result.pas_score, "category": pas_result.category.value}
            )

        return GateCheckResult(
            gate_number=2,
            gate_name="Parcel Attribution & Title Reconciliation",
            passed=True,
            telemetry_metadata={"pas_score": pas_result.pas_score, "category": pas_result.category.value}
        )

    @staticmethod
    def verify_gate_3_encumbrance_equity(equity_result: EquityWaterfallResult) -> GateCheckResult:
        """Gate 3: Encumbrance & Net Equity Audit.
        Enforces Net Equity >= $50,000 and Equity Percentage >= 30.0%.
        """
        if not equity_result.gate_3_passed:
            return GateCheckResult(
                gate_number=3,
                gate_name="Encumbrance & Net Equity Audit",
                passed=False,
                failure_reason=equity_result.disqualification_reason,
                telemetry_metadata={
                    "net_equity": equity_result.net_actionable_equity,
                    "equity_percentage": equity_result.equity_percentage,
                    "tier": equity_result.tier.value
                }
            )

        return GateCheckResult(
            gate_number=3,
            gate_name="Encumbrance & Net Equity Audit",
            passed=True,
            telemetry_metadata={
                "net_equity": equity_result.net_actionable_equity,
                "equity_percentage": equity_result.equity_percentage,
                "tier": equity_result.tier.value
            }
        )

    @staticmethod
    def verify_gate_4_fiduciary_authority(
        authority_tier: AuthorityTier,
        has_contested_caveats: bool
    ) -> GateCheckResult:
        """Gate 4: Fiduciary Authority Verification.
        Quarantines contested caveats and unresolvable intestate disputes.
        """
        if has_contested_caveats or authority_tier == AuthorityTier.TIER_4_UNRESOLVED:
            return GateCheckResult(
                gate_number=4,
                gate_name="Fiduciary Authority Verification",
                passed=False,
                failure_reason="Estate has active caveats, competing petitions, or unresolved signatory authority.",
                telemetry_metadata={"authority_tier": authority_tier.value, "has_caveats": has_contested_caveats}
            )

        return GateCheckResult(
            gate_number=4,
            gate_name="Fiduciary Authority Verification",
            passed=True,
            telemetry_metadata={"authority_tier": authority_tier.value}
        )

    @staticmethod
    def verify_gate_5_contact_scrubbing(
        primary_phone_active: bool,
        dnc_filtered: bool,
        is_attorney_quarantined: bool
    ) -> GateCheckResult:
        """Gate 5: Decision-Maker Contact Scrubbing.
        Requires verified active carrier line, DNC status check, and attorney quarantine.
        """
        if not primary_phone_active:
            return GateCheckResult(
                gate_number=5,
                gate_name="Decision-Maker Contact Scrubbing",
                passed=False,
                failure_reason="Primary decision-maker mobile phone is disconnected or failed carrier HLR dip."
            )

        if not dnc_filtered:
            return GateCheckResult(
                gate_number=5,
                gate_name="Decision-Maker Contact Scrubbing",
                passed=False,
                failure_reason="National Do-Not-Call (DNC) registry verification has not been scrubbed."
            )

        if not is_attorney_quarantined:
            return GateCheckResult(
                gate_number=5,
                gate_name="Decision-Maker Contact Scrubbing",
                passed=False,
                failure_reason="Estate attorney gatekeeper has not been quarantined from primary outreach."
            )

        return GateCheckResult(
            gate_number=5,
            gate_name="Decision-Maker Contact Scrubbing",
            passed=True
        )

    @staticmethod
    def verify_gate_6_predelivery_certification(
        scoring_result: OpportunityScoringResult,
        evidence_records_count: int,
        is_in_partner_buybox: bool = True
    ) -> GateCheckResult:
        """Gate 6: Pre-Delivery Final Certification.
        Ensures partner buy-box compatibility, minimum score (>=60), and evidence attachments.
        """
        if not is_in_partner_buybox:
            return GateCheckResult(
                gate_number=6,
                gate_name="Pre-Delivery Final Certification",
                passed=False,
                failure_reason="Property zip code or physical asset specs fall outside partner buy-box."
            )

        if scoring_result.composite_viability_score < 60 or scoring_result.priority_tier == PriorityTier.DISQUALIFIED:
            return GateCheckResult(
                gate_number=6,
                gate_name="Pre-Delivery Final Certification",
                passed=False,
                failure_reason=f"Viability score ({scoring_result.composite_viability_score}) is below standard delivery threshold (60).",
                telemetry_metadata={"score": scoring_result.composite_viability_score, "priority": scoring_result.priority_tier.value}
            )

        # Requires at least 2 immutable evidence records (e.g. Court Petition + Recorded Deed/Tax Card)
        if evidence_records_count < 2:
            return GateCheckResult(
                gate_number=6,
                gate_name="Pre-Delivery Final Certification",
                passed=False,
                failure_reason="Insufficient cryptographic evidence records packaged with file (< 2 documents).",
                telemetry_metadata={"evidence_records_count": evidence_records_count}
            )

        return GateCheckResult(
            gate_number=6,
            gate_name="Pre-Delivery Final Certification",
            passed=True,
            telemetry_metadata={
                "composite_viability_score": scoring_result.composite_viability_score,
                "priority_tier": scoring_result.priority_tier.value
            }
        )

    @classmethod
    def evaluate_all_gates(
        cls,
        case_number: str,
        filing_date_valid: bool,
        petition_pdf_sha256: Optional[str],
        pas_result: ParcelAttributionResult,
        equity_result: EquityWaterfallResult,
        authority_tier: AuthorityTier,
        has_contested_caveats: bool,
        primary_phone_active: bool,
        dnc_filtered: bool,
        is_attorney_quarantined: bool,
        scoring_result: OpportunityScoringResult,
        evidence_records_count: int,
        is_in_partner_buybox: bool = True
    ) -> QualityControlAuditSummary:
        """Executes the full 6-gate sequential audit and produces certification status."""
        results: List[GateCheckResult] = []

        # Gate 1
        g1 = cls.verify_gate_1_docket_integrity(case_number, filing_date_valid, petition_pdf_sha256)
        results.append(g1)
        if not g1.passed:
            return QualityControlAuditSummary(
                is_fully_certified=False, failed_gate=1, gate_results=results, disqualification_reason=g1.failure_reason
            )

        # Gate 2
        g2 = cls.verify_gate_2_parcel_attribution(pas_result)
        results.append(g2)
        if not g2.passed:
            return QualityControlAuditSummary(
                is_fully_certified=False, failed_gate=2, gate_results=results, disqualification_reason=g2.failure_reason
            )

        # Gate 3
        g3 = cls.verify_gate_3_encumbrance_equity(equity_result)
        results.append(g3)
        if not g3.passed:
            return QualityControlAuditSummary(
                is_fully_certified=False, failed_gate=3, gate_results=results, disqualification_reason=g3.failure_reason
            )

        # Gate 4
        g4 = cls.verify_gate_4_fiduciary_authority(authority_tier, has_contested_caveats)
        results.append(g4)
        if not g4.passed:
            return QualityControlAuditSummary(
                is_fully_certified=False, failed_gate=4, gate_results=results, disqualification_reason=g4.failure_reason
            )

        # Gate 5
        g5 = cls.verify_gate_5_contact_scrubbing(primary_phone_active, dnc_filtered, is_attorney_quarantined)
        results.append(g5)
        if not g5.passed:
            return QualityControlAuditSummary(
                is_fully_certified=False, failed_gate=5, gate_results=results, disqualification_reason=g5.failure_reason
            )

        # Gate 6
        g6 = cls.verify_gate_6_predelivery_certification(scoring_result, evidence_records_count, is_in_partner_buybox)
        results.append(g6)
        if not g6.passed:
            return QualityControlAuditSummary(
                is_fully_certified=False, failed_gate=6, gate_results=results, disqualification_reason=g6.failure_reason
            )

        return QualityControlAuditSummary(
            is_fully_certified=True,
            failed_gate=None,
            gate_results=results,
            disqualification_reason=None
        )
