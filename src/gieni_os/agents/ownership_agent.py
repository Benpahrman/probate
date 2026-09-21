"""
Ownership Agent
Solves deed vesting, title complexity, and net equity via OwnershipEngine.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.ownership_engine import OwnershipEngine

class OwnershipAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_ownership",
            agent_name="Ownership Agent",
            version="2.0.0"
        )

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("property_id") and payload.get("decedent_name"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid ownership payload: property_id and decedent_name required.")

        grantee_names = payload.get("grantee_names") or [payload["decedent_name"]]

        ownership_rec = OwnershipEngine.analyze_vesting(
            property_id=payload["property_id"],
            decedent_name=payload["decedent_name"],
            grantee_names=grantee_names,
            has_mortgage_cloud=payload.get("has_mortgage_cloud", False)
        )

        return {
            "status": "OWNERSHIP_RESOLVED",
            "ownership_record": ownership_rec,
            "vesting_type": ownership_rec.vesting_type.value,
            "title_complexity": ownership_rec.title_complexity_score,
            "net_equity": ownership_rec.waterfall.net_equity,
            "curative_required": ownership_rec.curative_required,
            "curative_notes": ownership_rec.curative_notes
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
