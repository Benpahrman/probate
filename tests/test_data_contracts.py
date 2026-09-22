import uuid
from datetime import datetime, timezone
import pytest
from app.core.database import Base
from app.models.enums import (
    LifecycleStage,
    PriorityTier,
    AuthorityTier,
    LettersStatus,
    PowerScope,
    VestingType
)
from app.schemas.events import (
    PropertyIdentifiedEvent,
    OwnershipUpdatedEvent,
    AuthorityUpdatedEvent,
    OpportunityScoredEvent,
    SitusAddressDTO,
    FiduciaryContactDTO
)
import app.models  # Ensure all models are registered on Base.metadata


def test_sqlalchemy_metadata_registration():
    """Verify all 17 canonical domain tables register on Base.metadata."""
    registered_tables = Base.metadata.tables.keys()
    required_tables = [
        "counties",
        "persons",
        "contact_points",
        "probate_cases",
        "properties",
        "property_assessments",
        "encumbrances",
        "tax_liens",
        "ownership_assessments",
        "control_assessments",
        "authority_assessments",
        "opportunities",
        "clients",
        "territory_agreements",
        "opportunity_deliveries",
        "evidence_records",
        "tasks_exceptions"
    ]
    for table in required_tables:
        assert table in registered_tables, f"Missing table {table} in metadata."


def test_property_identified_event_contract():
    """Verify serialization of Property.Identified Event Contract."""
    event = PropertyIdentifiedEvent(
        eventId=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        caseId=uuid.uuid4(),
        propertyId=uuid.uuid4(),
        countyFips="48201",
        apn="041-280-001-002",
        situsAddress=SitusAddressDTO(
            street="1428 Elm Street",
            city="Houston",
            state="TX",
            zip="77002"
        ),
        pasScore=94.5,
        attributionMethod="GIS_NAME_STREET_MATCH"
    )
    payload = event.model_dump()
    assert payload["eventType"] == "Property.Identified"
    assert payload["pasScore"] == 94.5
    assert payload["situsAddress"]["state"] == "TX"


def test_ownership_updated_event_contract():
    """Verify serialization of Ownership.Updated Event Contract."""
    event = OwnershipUpdatedEvent(
        eventId=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        propertyId=uuid.uuid4(),
        vestingType=VestingType.SOLE_FEE_SIMPLE,
        deceasedTitleholder="Robert E. Johnson",
        avmMarketValue=345000.00,
        totalEncumbrances=85000.00,
        netEquity=260000.00,
        equityPct=0.7536,
        ownershipComplexityScore=25
    )
    payload = event.model_dump()
    assert payload["eventType"] == "Ownership.Updated"
    assert payload["netEquity"] == 260000.00
    assert payload["ownershipComplexityScore"] == 25


def test_authority_updated_event_contract():
    """Verify serialization of Authority.Updated Event Contract."""
    event = AuthorityUpdatedEvent(
        eventId=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        caseId=uuid.uuid4(),
        authorityTier=AuthorityTier.TIER_1_CONFIRMED,
        lettersStatus=LettersStatus.ISSUED,
        powerScope=PowerScope.FULL_INDEPENDENT_ADMINISTRATION,
        fiduciary=FiduciaryContactDTO(
            personId="per_991823-aa11",
            name="Sarah Johnson Miller",
            relationship="Daughter",
            primaryPhone="+18325551928",
            phoneCarrierValid=True,
            dncScrubbed=True
        ),
        attorneyQuarantined=True
    )
    payload = event.model_dump()
    assert payload["eventType"] == "Authority.Updated"
    assert payload["authorityTier"] == "TIER_1_CONFIRMED"
    assert payload["attorneyQuarantined"] is True


def test_opportunity_scored_event_contract():
    """Verify serialization of Opportunity.Scored Event Contract."""
    event = OpportunityScoredEvent(
        eventId=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        opportunityId="opp_441890-ee88",
        compositeViabilityScore=88,
        priorityTier=PriorityTier.PRIORITY_A,
        dealFrictionScore=18,
        dispatchSLA="FLASH_ALERT_4_HOUR"
    )
    payload = event.model_dump()
    assert payload["eventType"] == "Opportunity.Scored"
    assert payload["compositeViabilityScore"] == 88
    assert payload["priorityTier"] == "PRIORITY_A"
