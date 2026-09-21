"""
Domain Models for Commercial Delivery, CRM Adapters & Flash Dispatch
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import time
from pydantic import BaseModel, Field, ConfigDict

class DeliveryChannel(str, Enum):
    CRM_WEBHOOK = "CRM_WEBHOOK"
    SMS_FLASH = "SMS_FLASH"
    EMAIL_DOSSIER = "EMAIL_DOSSIER"
    PDF_EXPORT = "PDF_EXPORT"

class CRMPlatform(str, Enum):
    PODIO = "PODIO"
    GOHIGHLEVEL = "GOHIGHLEVEL"
    SALESFORCE = "SALESFORCE"
    REI_BLACKBOOK = "REI_BLACKBOOK"
    GENERIC_WEBHOOK = "GENERIC_WEBHOOK"

class FlashAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")

    opportunity_id: str
    recipient_phone: str
    priority_tier: str
    alert_headline: str
    property_summary: str
    net_equity: float
    composite_score: int
    sent_at: float = Field(default_factory=time.time)
    sla_status: str = "DELIVERED_UNDER_4_HOURS"

class DeliveryDispatchRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dispatch_id: str
    opportunity_id: str
    client_id: str
    channel: DeliveryChannel
    platform: CRMPlatform
    endpoint_url: str
    status: str = "SUCCESS"  # SUCCESS, FAILED, RETRYING
    http_status_code: int = 200
    latency_ms: int = 42
    hmac_signature: str
    attempts: int = 1
    payload: Dict[str, Any] = Field(default_factory=dict)
    flash_alert: Optional[FlashAlert] = None
    dispatched_at: float = Field(default_factory=time.time)
