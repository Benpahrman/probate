"""
Domain Model: Decision-Maker Contact Enrichment & Skip-Tracing
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class LineType(str, Enum):
    WIRELESS = "WIRELESS"
    LANDLINE = "LANDLINE"
    VOIP = "VOIP"

@dataclass
class PhoneRecord:
    number: str
    line_type: LineType
    carrier: str
    confidence_score: float              # 0.0 to 1.0
    is_dnc: bool = False
    is_primary: bool = False

@dataclass
class ContactEnrichmentRecord:
    target_name: str
    relationship: str
    primary_phone: Optional[str]
    phones: List[PhoneRecord]
    verified_email: Optional[str]
    mailing_address: str
    situs_is_mailing: bool
    skip_trace_confidence: float         # 0-100%
    recommended_outreach_channel: str    # "PHONE_CALL", "DIRECT_MAIL", "SMS"
    outreach_script_template: str
