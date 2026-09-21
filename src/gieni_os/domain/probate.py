"""
Domain Model: Probate Case & Court Docket
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

class CaseStatus(str, Enum):
    OPEN = "OPEN"
    PENDING_REVIEW = "PENDING_REVIEW"
    LETTERS_ISSUED = "LETTERS_ISSUED"
    DISPUTED = "DISPUTED"
    CLOSED = "CLOSED"

@dataclass
class DocketRecord:
    case_number: str
    county_id: str
    decedent_name: str
    filing_date: date
    attorney_name: Optional[str] = None
    petitioner_name: Optional[str] = None
    case_type: str = "Probate"
    raw_court_data: Dict[str, Any] = field(default_factory=dict)
