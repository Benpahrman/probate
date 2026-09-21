"""
Authority Agent
Resolves statutory fiduciary authority and court supervision via AuthorityEngine.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.authority_engine import AuthorityEngine

class AuthorityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_authority",
            agent_name="Authority Agent",
            version="2.0.0"
        )

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("case_number") and payload.get("property_id") and payload.get("petitioner_name"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid authority payload: case_number, property_id, and petitioner_name required.")

        authority_rec = AuthorityEngine.evaluate_authority(
            case_number=payload["case_number"],
            property_id=payload["property_id"],
            petitioner_name=payload["petitioner_name"],
            docket_entries=payload.get("docket_entries", []),
            will_filed=payload.get("will_filed", True),
            is_contested=payload.get("is_contested", False)
        )

        return {
            "status": "AUTHORITY_RESOLVED",
            "authority_record": authority_rec,
            "authority_tier": authority_rec.authority_tier.value,
            "fiduciary_name": authority_rec.fiduciary_name,
            "letters_status": authority_rec.letters_status.value,
            "statutory_powers": authority_rec.statutory_powers,
            "requires_human_verification": authority_rec.requires_human_verification,
            "evidence_citation": authority_rec.evidence_citation
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
