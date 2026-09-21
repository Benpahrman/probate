"""
Gieni OS Canonical Event DTOs (Pydantic v2)
Strict, immutable data transfer objects for inter-service event contracts.
Used by the test suite, ingest workers, and API routes.

Transplanted from backend/app/schemas/events.py.
Imports rewritten: app.models.enums → gieni_os.domain.enums
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from gieni_os.domain.enums import AuthorityTier, LettersStatus, PowerScope, PriorityTier, VestingType


class SitusAddressDTO(BaseModel):
    street: str
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip: str = Field(..., min_length=5, max_length=10)


class PropertyIdentifiedEvent(BaseModel):
    """Event Contract 1: Property.Identified"""
    eventType: str = "Property.Identified"
    eventId: UUID
    timestamp: datetime
    caseId: UUID
    propertyId: UUID
    countyFips: str = Field(..., min_length=5, max_length=5)
    apn: str
    situsAddress: SitusAddressDTO
    pasScore: float = Field(..., ge=0.0, le=100.0)
    attributionMethod: str

    model_config = ConfigDict(extra="forbid")


class OwnershipUpdatedEvent(BaseModel):
    """Event Contract 2: Ownership.Updated"""
    eventType: str = "Ownership.Updated"
    eventId: UUID
    timestamp: datetime
    propertyId: UUID
    vestingType: VestingType
    deceasedTitleholder: str
    avmMarketValue: float = Field(..., ge=0.0)
    totalEncumbrances: float = Field(..., ge=0.0)
    netEquity: float
    equityPct: float
    ownershipComplexityScore: int = Field(..., ge=10, le=100)

    model_config = ConfigDict(extra="forbid")


class FiduciaryContactDTO(BaseModel):
    personId: str
    name: str
    relationship: str
    primaryPhone: str
    phoneCarrierValid: bool
    dncScrubbed: bool


class AuthorityUpdatedEvent(BaseModel):
    """Event Contract 3: Authority.Updated"""
    eventType: str = "Authority.Updated"
    eventId: UUID
    timestamp: datetime
    caseId: UUID
    authorityTier: AuthorityTier
    lettersStatus: LettersStatus
    powerScope: PowerScope
    fiduciary: FiduciaryContactDTO
    attorneyQuarantined: bool

    model_config = ConfigDict(extra="forbid")


class OpportunityScoredEvent(BaseModel):
    """Event Contract 4: Opportunity.Scored"""
    eventType: str = "Opportunity.Scored"
    eventId: UUID
    timestamp: datetime
    opportunityId: str
    compositeViabilityScore: int = Field(..., ge=0, le=100)
    priorityTier: PriorityTier
    dealFrictionScore: int = Field(..., ge=0, le=100)
    dispatchSLA: str

    model_config = ConfigDict(extra="forbid")
