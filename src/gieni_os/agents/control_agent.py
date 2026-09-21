"""
Control Agent
Maps family and social dynamics into Knowledge Graph & classifies the Control Archetype via ControlEngine.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.control_engine import ControlEngine

class ControlAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_control",
            agent_name="Control Agent",
            version="2.0.0"
        )

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("fiduciary_name") and payload.get("property_address"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid control payload: fiduciary_name and property_address required.")

        profile = ControlEngine.classify_control_archetype(
            fiduciary_name=payload["fiduciary_name"],
            fiduciary_address=payload.get("fiduciary_address") or payload["property_address"],
            property_situs=payload["property_address"],
            heir_names=payload.get("heir_names", [payload["fiduciary_name"]]),
            resident_names=payload.get("resident_names", [payload["fiduciary_name"]]),
            attorney_name=payload.get("attorney_name")
        )

        return {
            "status": "CONTROL_MAPPED",
            "control_profile": profile,
            "control_archetype": profile.archetype.value,
            "occupancy_status": profile.occupancy_status.value,
            "friction_rating": profile.friction_rating,
            "primary_decision_maker": profile.primary_decision_maker.name,
            "attorney_bypass_strategy": profile.attorney_bypass_strategy
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
