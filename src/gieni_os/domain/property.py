"""
Domain Model: Property & Parcel Identity
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SitusAddress:
    street: str
    city: str
    state: str
    zip_code: str
    unit: Optional[str] = None

    def full_address(self) -> str:
        u = f" {self.unit}" if self.unit else ""
        return f"{self.street}{u}, {self.city}, {self.state} {self.zip_code}".strip()

@dataclass
class PropertyRecord:
    property_id: str
    county_id: str
    apn: Optional[str] = None
    address: SitusAddress = None
    pas_score: float = 0.0              # Property Alignment Score (0-100)
    assessed_value: Optional[float] = None
    property_type: str = "SINGLE_FAMILY"
    subdivision: Optional[str] = None
