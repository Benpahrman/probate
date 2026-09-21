"""
Commercial Delivery Agent
Assembles the 8-Profile POF v2.0 and dispatches to Partner CRMs via DeliveryEngine.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.delivery_engine import DeliveryEngine
from gieni_os.domain.delivery import CRMPlatform

class DeliveryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_delivery",
            agent_name="Commercial Delivery Agent",
            version="2.0.0"
        )
        self.engine = DeliveryEngine()

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("opportunity_id"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid delivery payload: opportunity_id required.")

        opp_id = payload["opportunity_id"]
        client_id = payload.get("client_id", "CLIENT_001")
        raw_platform = payload.get("crm_platform", CRMPlatform.GOHIGHLEVEL.value)
        try:
            platform = CRMPlatform(raw_platform)
        except ValueError:
            platform = CRMPlatform.GOHIGHLEVEL

        dispatch_record = self.engine.dispatch(
            context=payload,
            client_id=client_id,
            platform=platform,
            webhook_secret=payload.get("webhook_secret", "gieni_secret_key_prod"),
            endpoint_url=payload.get("endpoint_url", "https://api.leadconduit.com/v2/webhook")
        )

        return {
            "status": "DELIVERED",
            "opportunity_id": opp_id,
            "dispatch_id": dispatch_record.dispatch_id,
            "client_id": client_id,
            "crm_platform": platform.value,
            "latency_ms": dispatch_record.latency_ms,
            "hmac_signature": dispatch_record.hmac_signature,
            "flash_alert_sent": dispatch_record.flash_alert is not None,
            "dispatch_record": dispatch_record
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
