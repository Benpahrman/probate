"""
Property Agent
Executes property discovery and parcel matching via PropertyEngine.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.property_engine import PropertyEngine

class PropertyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_property",
            agent_name="Property Agent",
            version="2.0.0"
        )

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("raw_address") and payload.get("county_id"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid property discovery payload: raw_address and county_id required.")

        property_rec = PropertyEngine.reconcile_parcel(
            raw_address=payload["raw_address"],
            county_id=payload["county_id"],
            decedent_name=payload.get("decedent_name", ""),
            candidate_apn=payload.get("apn")
        )

        return {
            "status": "PROPERTY_MATCHED",
            "property_record": property_rec,
            "property_id": property_rec.property_id,
            "apn": property_rec.apn,
            "pas_score": property_rec.pas_score,
            "full_address": property_rec.address.full_address()
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
