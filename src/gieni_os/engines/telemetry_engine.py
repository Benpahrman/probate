"""
Closed-Loop Telemetry Ingestion & RL Friction Recalibration Engine
Consumes partner disposition outcomes, tracks conversion velocities, and recalibrates county weights.
"""

from typing import Dict, Any, List, Optional
import time
import logging

from gieni_os.domain.telemetry import (
    DispositionStage,
    DispositionRecord,
    CountyCalibrationProfile
)
from gieni_os.events.schemas import TelemetryIngestedEvent
from gieni_os.learning.reinforcement import ReinforcementLearningEngine

logger = logging.getLogger("TelemetryEngine")

class TelemetryEngine:
    def __init__(self):
        self.rl_engine = ReinforcementLearningEngine()
        self.history: List[DispositionRecord] = []

    def record_disposition(
        self,
        opportunity_id: str,
        client_id: str,
        stage: DispositionStage,
        contact_latency_hours: float = 1.2,
        offer_amount: float = 0.0,
        assignment_fee_realized: float = 0.0,
        decision_maker_accurate: bool = True,
        disposition_notes: Optional[str] = None
    ) -> DispositionRecord:
        record = DispositionRecord(
            opportunity_id=opportunity_id,
            client_id=client_id,
            disposition_stage=stage,
            contact_latency_hours=contact_latency_hours,
            offer_amount=offer_amount,
            assignment_fee_realized=assignment_fee_realized,
            decision_maker_accurate=decision_maker_accurate,
            disposition_notes=disposition_notes,
            recorded_at=time.time()
        )
        self.history.append(record)

        # Feed into reinforcement learning engine
        event = TelemetryIngestedEvent(
            opportunityId=opportunity_id,
            clientId=client_id,
            dispositionStage=stage.value,
            contactOutcome="OFFER_ACCEPTED" if stage == DispositionStage.CLOSED_WON else stage.value,
            decisionMakerAccurate=decision_maker_accurate,
            wholesaleFeeRealized=assignment_fee_realized
        )
        self.rl_engine.ingest_telemetry_event(event)

        logger.info(
            f"[{opportunity_id}] Telemetry recorded: {stage.value} "
            f"(Fee: ${assignment_fee_realized:,.2f}, Latency: {contact_latency_hours:.1f}h)"
        )
        return record

    def recalibrate_county(self, county_fips: str = "53033") -> CountyCalibrationProfile:
        """
        Runs RL Bayesian feedback loop to tune friction coefficients and feature weights.
        """
        raw_recalibration = self.rl_engine.recalibrate(county_fips)

        return CountyCalibrationProfile(
            county_fips=county_fips,
            sample_size=raw_recalibration["sample_size"],
            closed_won_count=raw_recalibration["closed_won_count"],
            win_rate=raw_recalibration["closed_won_count"] / max(1, raw_recalibration["sample_size"]),
            calibrated_friction_coefficient=raw_recalibration["calibrated_county_friction_coefficient"],
            updated_feature_weights=raw_recalibration["updated_feature_weights"],
            quarterly_predictive_accuracy_gain_pct=raw_recalibration["quarterly_predictive_accuracy_gain_pct"]
        )
