"""
Disposition Telemetry Agent
Ingests partner commercial outcomes, updates closed-loop telemetry, and triggers RL recalibration.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.telemetry_engine import TelemetryEngine
from gieni_os.domain.telemetry import DispositionStage

class TelemetryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_telemetry",
            agent_name="Disposition Telemetry Agent",
            version="2.0.0"
        )
        self.engine = TelemetryEngine()

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("opportunity_id") and payload.get("disposition_stage"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid telemetry payload: opportunity_id and disposition_stage required.")

        opp_id = payload["opportunity_id"]
        client_id = payload.get("client_id", "CLIENT_001")
        raw_stage = payload["disposition_stage"]
        try:
            stage = DispositionStage(raw_stage)
        except ValueError:
            stage = DispositionStage.CLOSED_WON if "WON" in raw_stage.upper() else DispositionStage.CLOSED_LOST

        latency = float(payload.get("contact_latency_hours", 1.2))
        offer = float(payload.get("offer_amount", 0.0))
        fee = float(payload.get("assignment_fee_realized", 0.0))
        accurate = bool(payload.get("decision_maker_accurate", True))
        notes = payload.get("disposition_notes")

        record = self.engine.record_disposition(
            opportunity_id=opp_id,
            client_id=client_id,
            stage=stage,
            contact_latency_hours=latency,
            offer_amount=offer,
            assignment_fee_realized=fee,
            decision_maker_accurate=accurate,
            disposition_notes=notes
        )

        county_fips = payload.get("county_fips", "53033")
        recalibration = self.engine.recalibrate_county(county_fips)

        return {
            "status": "TELEMETRY_INGESTED",
            "opportunity_id": opp_id,
            "disposition_stage": stage.value,
            "assignment_fee_realized": fee,
            "disposition_record": record,
            "county_recalibration": recalibration
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
