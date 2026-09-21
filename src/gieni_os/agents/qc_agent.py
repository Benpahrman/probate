"""
Quality Control Agent
Executes Automated 6-Gate Quality Control Pass and notarizes certification seals.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.qc_engine import QCEngine

class QCAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_qc",
            agent_name="Quality Control Certification Agent",
            version="2.0.0"
        )
        self.engine = QCEngine()

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("opportunity_id") and payload.get("opportunity_score"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid QC payload: opportunity_id and opportunity_score required.")

        report = self.engine.validate_opportunity(
            opportunity_id=payload["opportunity_id"],
            property_record=payload.get("property_record"),
            ownership_record=payload.get("ownership_record"),
            authority_record=payload.get("authority_record"),
            control_profile=payload.get("control_profile"),
            contact_record=payload.get("contact_record"),
            score=payload["opportunity_score"]
        )

        return {
            "status": "QC_CERTIFIED" if report.all_passed else "QC_FAILED",
            "opportunity_id": payload["opportunity_id"],
            "qc_report": report,
            "all_passed": report.all_passed,
            "certification_stamp": report.certification_stamp,
            "requires_hitl": report.requires_hitl,
            "hitl_reasons": report.hitl_reasons
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
