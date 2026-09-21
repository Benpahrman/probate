"""
Contact Agent
Enriches Decision-Maker contact info, phone lines, and generates tailored outreach scripts.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.contact_engine import ContactEngine
from gieni_os.domain.control import ControlArchetype

class ContactAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_contact",
            agent_name="Contact Agent",
            version="2.0.0"
        )

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("target_name") and payload.get("situs_address"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid contact payload: target_name and situs_address required.")

        archetype_str = payload.get("control_archetype", ControlArchetype.MODEL_1_UNIFIED.value)
        try:
            archetype = ControlArchetype(archetype_str)
        except ValueError:
            archetype = ControlArchetype.MODEL_1_UNIFIED

        enrichment = ContactEngine.enrich_decision_maker(
            target_name=payload["target_name"],
            relationship=payload.get("relationship", "Personal Representative"),
            mailing_address=payload.get("mailing_address") or payload["situs_address"],
            situs_address=payload["situs_address"],
            control_archetype=archetype,
            raw_phones=payload.get("raw_phones")
        )

        return {
            "status": "CONTACTS_FOUND",
            "enrichment_record": enrichment,
            "target_name": enrichment.target_name,
            "primary_phone": enrichment.primary_phone,
            "verified_email": enrichment.verified_email,
            "skip_trace_confidence": enrichment.skip_trace_confidence,
            "outreach_channel": enrichment.recommended_outreach_channel,
            "outreach_script": enrichment.outreach_script_template
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
