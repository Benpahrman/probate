"""
Automated 6-Gate Quality Control Engine (QCA)
Validates compliance across Physical Property, Ownership, Equity, Control, Authority, and Viability.
"""

from typing import Dict, Any, List, Optional
import hashlib
import time
import logging

from gieni_os.domain.qc import GateResult, QCValidationReport
from gieni_os.domain.scoring import OpportunityScore, PriorityTier
from gieni_os.domain.property import PropertyRecord
from gieni_os.domain.ownership import OwnershipRecord
from gieni_os.domain.authority import FiduciaryAuthorityRecord, AuthorityTier
from gieni_os.domain.control import ControlProfile
from gieni_os.domain.contact import ContactEnrichmentRecord

logger = logging.getLogger("QCEngine")

class QCEngine:
    """
    Automated 6-Gate Quality Control validator:
    Gate 1: Physical Asset & Property Match (PAS >= 70.0)
    Gate 2: Legal Ownership & Title Vesting (Resolved title, complexity <= 5)
    Gate 3: Net Equity Waterfall (Net equity >= $50k or >= 25% of AVM)
    Gate 4: Control Path & Reachable Decision-Maker (Reachable signatory, phone confidence >= 70%)
    Gate 5: Fiduciary Authority Resolution (Tier 1, 2, or 3, authorized signatory)
    Gate 6: Composite Score & Friction Threshold (Score >= 50, DFS <= 25)
    """

    def validate_opportunity(
        self,
        opportunity_id: str,
        property_record: Optional[PropertyRecord],
        ownership_record: Optional[OwnershipRecord],
        authority_record: Optional[FiduciaryAuthorityRecord],
        control_profile: Optional[ControlProfile],
        contact_record: Optional[ContactEnrichmentRecord],
        score: OpportunityScore
    ) -> QCValidationReport:
        gates: List[GateResult] = []
        hitl_reasons: List[str] = []

        # Gate 1: Physical Asset & Property Match (PAS >= 70.0)
        pas = property_record.pas_score if property_record else 0.0
        g1_passed = pas >= 70.0
        g1_msg = f"Parcel matched with PAS {pas:.1f}/100" if g1_passed else f"PAS {pas:.1f} below 70.0 threshold"
        gates.append(GateResult(
            gate_number=1,
            gate_name="Physical Asset & Property Match",
            passed=g1_passed,
            score=pas,
            threshold=70.0,
            rationale=g1_msg
        ))
        if not g1_passed:
            hitl_reasons.append("Gate 1 Failed: Low parcel attribution confidence.")

        # Gate 2: Legal Ownership & Title Vesting
        complexity = ownership_record.title_complexity_score if ownership_record else 10
        g2_passed = complexity <= 5
        g2_msg = f"Title vesting confirmed (Complexity {complexity}/10)" if g2_passed else f"High title complexity ({complexity}/10)"
        gates.append(GateResult(
            gate_number=2,
            gate_name="Legal Ownership & Title Vesting",
            passed=g2_passed,
            score=float(complexity),
            threshold=5.0,
            rationale=g2_msg
        ))
        if not g2_passed:
            hitl_reasons.append("Gate 2 Failed: Severe title complexity or fractional heir clouds.")

        # Gate 3: Net Equity Waterfall
        waterfall_obj = None
        if ownership_record:
            waterfall_obj = getattr(ownership_record, "waterfall", None) or getattr(ownership_record, "equity_waterfall", None)

        net_equity = getattr(waterfall_obj, "net_equity", 0.0) if waterfall_obj else 0.0
        est_value = getattr(waterfall_obj, "estimated_market_value", None) or getattr(waterfall_obj, "estimated_value", 1.0) if waterfall_obj else 1.0
        equity_ratio = (net_equity / est_value) if est_value > 0 else 0.0
        g3_passed = net_equity >= 50000.0 or equity_ratio >= 0.25
        g3_msg = f"Net equity: ${net_equity:,.2f} ({equity_ratio*100:.1f}%)" if g3_passed else f"Insufficient equity (${net_equity:,.2f})"
        gates.append(GateResult(
            gate_number=3,
            gate_name="Net Equity Waterfall",
            passed=g3_passed,
            score=float(net_equity),
            threshold=50000.0,
            rationale=g3_msg
        ))
        if not g3_passed:
            hitl_reasons.append("Gate 3 Failed: Thin or negative equity margin.")

        # Gate 4: Control Path & Reachable Decision-Maker
        has_reachable_dm = False
        phone_conf = 0.0
        if control_profile and control_profile.primary_decision_maker:
            has_reachable_dm = bool(control_profile.primary_decision_maker.phone)
        if contact_record:
            phone_conf = getattr(contact_record, "skip_trace_confidence", 0.0)
            if phone_conf <= 1.0:
                phone_conf = phone_conf * 100.0

        g4_passed = has_reachable_dm and (phone_conf >= 70.0)
        g4_msg = (
            f"Reachable fiduciary with verified phone (Confidence: {phone_conf:.1f}%)"
            if g4_passed else f"Fiduciary reachability unconfirmed or low phone confidence ({phone_conf:.1f}%)"
        )
        gates.append(GateResult(
            gate_number=4,
            gate_name="Control Path & Reachable Decision-Maker",
            passed=g4_passed,
            score=phone_conf,
            threshold=70.0,
            rationale=g4_msg
        ))
        if not g4_passed:
            hitl_reasons.append("Gate 4 Failed: No verified contact route to primary decision maker.")

        # Gate 5: Fiduciary Authority Resolution (Tier 1, 2, or 3)
        auth_tier = authority_record.authority_tier if authority_record else AuthorityTier.TIER_4_UNCERTAIN
        g5_passed = auth_tier in (AuthorityTier.TIER_1_CERTIFIED, AuthorityTier.TIER_2_PROBABLE, AuthorityTier.TIER_3_NON_PROBATE)
        g5_msg = f"Authority resolved as {auth_tier.value}" if g5_passed else "Statutory authority uncertain or contested"
        gates.append(GateResult(
            gate_number=5,
            gate_name="Fiduciary Authority Resolution",
            passed=g5_passed,
            score=1.0 if g5_passed else 0.0,
            threshold=1.0,
            rationale=g5_msg
        ))
        if not g5_passed:
            hitl_reasons.append("Gate 5 Failed: Authority contested or lack of probate letters.")

        # Gate 6: Composite Score & Friction Threshold (Score >= 50, DFS <= 25)
        comp_score = score.composite_score
        dfs = score.deal_friction.total_dfs
        g6_passed = comp_score >= 50 and dfs <= 25
        g6_msg = f"Composite score {comp_score}/100 with DFS {dfs}/35" if g6_passed else f"Composite score {comp_score} or DFS {dfs} exceeded threshold"
        gates.append(GateResult(
            gate_number=6,
            gate_name="Composite Score & Friction Threshold",
            passed=g6_passed,
            score=float(comp_score),
            threshold=50.0,
            rationale=g6_msg
        ))
        if not g6_passed:
            hitl_reasons.append("Gate 6 Failed: Composite score below viable threshold.")

        all_passed = all(g.passed for g in gates)

        # Borderline evaluation for HITL review
        requires_hitl = False
        if not all_passed:
            requires_hitl = True
        elif score.priority_tier == PriorityTier.PRIORITY_C or (60 <= comp_score < 75):
            requires_hitl = True
            hitl_reasons.append("Borderline Opportunity: Score between 60-74 requires human review.")

        # Cryptographic Notarization Stamp
        stamp = None
        ts = time.time()
        if all_passed:
            raw_seal = f"{opportunity_id}|{comp_score}|{ts}|GIENI_6_GATE_PASS"
            seal_hash = hashlib.sha256(raw_seal.encode("utf-8")).hexdigest()[:16].upper()
            stamp = f"GIENI_CERTIFIED_6_GATE_PASS_{seal_hash}"

        logger.info(
            f"[{opportunity_id}] 6-Gate Pass: {'SUCCESS' if all_passed else 'FAILED'} "
            f"(Passed: {sum(1 for g in gates if g.passed)}/6, HITL: {requires_hitl})"
        )

        return QCValidationReport(
            opportunity_id=opportunity_id,
            gates=gates,
            all_passed=all_passed,
            certification_stamp=stamp,
            certification_timestamp=ts,
            requires_hitl=requires_hitl,
            hitl_reasons=hitl_reasons
        )
