"""
Gieni OS Canonical SQLAlchemy 2.0 ORM — 17 Domain Tables
Single source of truth for all relational entities. Transplanted from the
backend/app/models/ module hierarchy and consolidated here.

Tables:
  1. counties
  2. persons
  3. contact_points
  4. probate_cases              (uq_case_per_county)
  5. properties                 (uq_apn_per_county)
  6. property_assessments
  7. encumbrances
  8. tax_liens
  9. ownership_assessments
 10. control_assessments
 11. authority_assessments
 12. opportunities
 13. clients
 14. territory_agreements       (uq_single_partner_per_county)
 15. opportunity_deliveries
 16. evidence_records
 17. tasks_exceptions
"""

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer,
    Numeric, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from gieni_os.domain.enums import (
    AuthorityTier,
    ControlArchetype,
    DeliveryChannel,
    ExceptionPriority,
    LettersStatus,
    LifecycleStage,
    PowerScope,
    PriorityTier,
    PropertyClass,
    VestingType,
)


# ── Declarative Base ───────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampedBase(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )


# ── Table 1: counties ──────────────────────────────────────────────────────────

class County(TimestampedBase):
    __tablename__ = "counties"

    county_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    county_fips: Mapped[str] = mapped_column(String(5), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), index=True, nullable=False)
    court_software_vendor: Mapped[str] = mapped_column(String(100), nullable=False)
    is_independent_admin_state: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monthly_filing_volume: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    median_home_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    friction_coefficient: Mapped[float] = mapped_column(Numeric(4, 3), default=1.000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    probate_cases: Mapped[List["ProbateCase"]] = relationship("ProbateCase", back_populates="county")
    properties: Mapped[List["Property"]] = relationship("Property", back_populates="county")
    territory_agreements: Mapped[List["TerritoryAgreement"]] = relationship(
        "TerritoryAgreement", back_populates="county"
    )


# ── Table 2: persons ──────────────────────────────────────────────────────────

class Person(TimestampedBase):
    __tablename__ = "persons"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name_suffix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_deceased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    date_of_death: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    contact_points: Mapped[List["ContactPoint"]] = relationship(
        "ContactPoint", back_populates="person", cascade="all, delete-orphan"
    )
    cases_as_decedent: Mapped[List["ProbateCase"]] = relationship(
        "ProbateCase", foreign_keys="ProbateCase.decedent_id", back_populates="decedent"
    )
    cases_as_petitioner: Mapped[List["ProbateCase"]] = relationship(
        "ProbateCase", foreign_keys="ProbateCase.petitioner_id", back_populates="petitioner"
    )


# ── Table 3: contact_points ───────────────────────────────────────────────────

class ContactPoint(TimestampedBase):
    __tablename__ = "contact_points"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.person_id", ondelete="CASCADE"), nullable=False
    )
    raw_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    e164_phone: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    is_mobile: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    phone_carrier_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dnc_scrubbed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    street_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    person: Mapped["Person"] = relationship("Person", back_populates="contact_points")


# ── Table 4: probate_cases ────────────────────────────────────────────────────

class ProbateCase(TimestampedBase):
    __tablename__ = "probate_cases"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    county_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("counties.county_id"), nullable=False
    )
    case_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    filing_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    decedent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False
    )
    petitioner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=True
    )
    attorney_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    attorney_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    attorney_quarantined: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_docket_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    invariant_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("county_id", "case_number", name="uq_case_per_county"),
    )

    # Relationships
    county: Mapped["County"] = relationship("County", back_populates="probate_cases")
    decedent: Mapped["Person"] = relationship(
        "Person", foreign_keys=[decedent_id], back_populates="cases_as_decedent"
    )
    petitioner: Mapped[Optional["Person"]] = relationship(
        "Person", foreign_keys=[petitioner_id], back_populates="cases_as_petitioner"
    )
    properties: Mapped[List["Property"]] = relationship("Property", back_populates="case")
    authority_assessment: Mapped[Optional["AuthorityAssessment"]] = relationship(
        "AuthorityAssessment", back_populates="case", uselist=False
    )
    control_assessment: Mapped[Optional["ControlAssessment"]] = relationship(
        "ControlAssessment", back_populates="case", uselist=False
    )
    opportunity: Mapped[Optional["Opportunity"]] = relationship(
        "Opportunity", back_populates="case", uselist=False
    )


# ── Table 5: properties ───────────────────────────────────────────────────────

class Property(TimestampedBase):
    __tablename__ = "properties"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("probate_cases.case_id"), nullable=False
    )
    county_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("counties.county_id"), nullable=False
    )
    apn: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    legal_description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    property_class: Mapped[PropertyClass] = mapped_column(
        String(50), default=PropertyClass.SINGLE_FAMILY, nullable=False
    )
    living_area_sqft: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lot_size_acres: Mapped[Optional[float]] = mapped_column(Numeric(8, 4), nullable=True)
    pas_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # 0 - 100
    is_vacant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("county_id", "apn", name="uq_apn_per_county"),
    )

    # Relationships
    case: Mapped["ProbateCase"] = relationship("ProbateCase", back_populates="properties")
    county: Mapped["County"] = relationship("County", back_populates="properties")
    assessments: Mapped[List["PropertyAssessment"]] = relationship(
        "PropertyAssessment", back_populates="property", cascade="all, delete-orphan"
    )
    encumbrances: Mapped[List["Encumbrance"]] = relationship(
        "Encumbrance", back_populates="property", cascade="all, delete-orphan"
    )
    tax_liens: Mapped[List["TaxLien"]] = relationship(
        "TaxLien", back_populates="property", cascade="all, delete-orphan"
    )
    ownership_assessment: Mapped[Optional["OwnershipAssessment"]] = relationship(
        "OwnershipAssessment", back_populates="property", uselist=False
    )


# ── Table 6: property_assessments ────────────────────────────────────────────

class PropertyAssessment(TimestampedBase):
    __tablename__ = "property_assessments"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False
    )
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    assessed_land_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    assessed_improvement_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    total_assessed_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    avm_market_estimate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationship
    property: Mapped["Property"] = relationship("Property", back_populates="assessments")


# ── Table 7: encumbrances ─────────────────────────────────────────────────────

class Encumbrance(TimestampedBase):
    __tablename__ = "encumbrances"

    encumbrance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False
    )
    encumbrance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(200), nullable=False)
    original_recording_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    original_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    instrument_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    property: Mapped["Property"] = relationship("Property", back_populates="encumbrances")


# ── Table 8: tax_liens ────────────────────────────────────────────────────────

class TaxLien(TimestampedBase):
    __tablename__ = "tax_liens"

    lien_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False
    )
    delinquent_years: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    amount_due: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_tax_certificate_sold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    redemption_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationship
    property: Mapped["Property"] = relationship("Property", back_populates="tax_liens")


# ── Table 9: ownership_assessments ───────────────────────────────────────────

class OwnershipAssessment(TimestampedBase):
    __tablename__ = "ownership_assessments"

    ownership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    vesting_type: Mapped[VestingType] = mapped_column(String(50), nullable=False)
    deceased_titleholder: Mapped[str] = mapped_column(String(200), nullable=False)
    avm_market_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_encumbrances: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    net_equity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    equity_pct: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    ownership_complexity_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 10 to 100

    # Relationship
    property: Mapped["Property"] = relationship("Property", back_populates="ownership_assessment")


# ── Table 10: control_assessments ────────────────────────────────────────────

class ControlAssessment(TimestampedBase):
    __tablename__ = "control_assessments"

    control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("probate_cases.case_id"), unique=True, nullable=False
    )
    control_archetype: Mapped[ControlArchetype] = mapped_column(String(50), nullable=False)
    controller_person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=True
    )
    is_resident_occupant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consensus_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    heir_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    case: Mapped["ProbateCase"] = relationship("ProbateCase", back_populates="control_assessment")
    controller: Mapped[Optional["Person"]] = relationship("Person")


# ── Table 11: authority_assessments ──────────────────────────────────────────

class AuthorityAssessment(TimestampedBase):
    __tablename__ = "authority_assessments"

    authority_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("probate_cases.case_id"), unique=True, nullable=False
    )
    authority_tier: Mapped[AuthorityTier] = mapped_column(String(50), nullable=False)
    letters_status: Mapped[LettersStatus] = mapped_column(String(50), nullable=False)
    power_scope: Mapped[PowerScope] = mapped_column(String(50), nullable=False)
    fiduciary_person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=True
    )
    court_confirmation_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    case: Mapped["ProbateCase"] = relationship("ProbateCase", back_populates="authority_assessment")
    fiduciary: Mapped[Optional["Person"]] = relationship("Person")


# ── Table 12: opportunities ───────────────────────────────────────────────────

class Opportunity(TimestampedBase):
    __tablename__ = "opportunities"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("probate_cases.case_id"), unique=True, nullable=False
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.property_id"), unique=True, nullable=False
    )
    lifecycle_stage: Mapped[LifecycleStage] = mapped_column(
        String(50), default=LifecycleStage.DISCOVERED, index=True, nullable=False
    )
    composite_viability_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)   # 0 to 100
    deal_friction_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)           # 0 to 35
    priority_tier: Mapped[PriorityTier] = mapped_column(
        String(50), default=PriorityTier.DISQUALIFIED, index=True, nullable=False
    )
    dispatch_sla: Mapped[str] = mapped_column(String(50), default="STANDARD_BATCH", nullable=False)
    is_qc_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    case: Mapped["ProbateCase"] = relationship("ProbateCase", back_populates="opportunity")
    property: Mapped["Property"] = relationship("Property")
    deliveries: Mapped[List["OpportunityDelivery"]] = relationship(
        "OpportunityDelivery", back_populates="opportunity"
    )


# ── Table 13: clients ─────────────────────────────────────────────────────────

class Client(TimestampedBase):
    __tablename__ = "clients"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    territory_agreements: Mapped[List["TerritoryAgreement"]] = relationship(
        "TerritoryAgreement", back_populates="client"
    )
    deliveries: Mapped[List["OpportunityDelivery"]] = relationship(
        "OpportunityDelivery", back_populates="client"
    )


# ── Table 14: territory_agreements ───────────────────────────────────────────

class TerritoryAgreement(TimestampedBase):
    __tablename__ = "territory_agreements"

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id"), nullable=False
    )
    county_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("counties.county_id"), nullable=False
    )
    monthly_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_cap_per_month: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("county_id", name="uq_single_partner_per_county"),  # County Exclusivity
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="territory_agreements")
    county: Mapped["County"] = relationship("County", back_populates="territory_agreements")


# ── Table 15: opportunity_deliveries ─────────────────────────────────────────

class OpportunityDelivery(TimestampedBase):
    __tablename__ = "opportunity_deliveries"

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.opportunity_id"), nullable=False
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id"), nullable=False
    )
    delivery_channel: Mapped[DeliveryChannel] = mapped_column(String(50), nullable=False)
    dispatched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_snapshot: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="deliveries")
    client: Mapped[Client] = relationship("Client", back_populates="deliveries")


# ── Table 16: evidence_records ────────────────────────────────────────────────

class EvidenceRecord(TimestampedBase):
    __tablename__ = "evidence_records"

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("probate_cases.case_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Petition, Letters, Deed, TaxCard
    storage_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # Relationship
    case: Mapped["ProbateCase"] = relationship("ProbateCase")


# ── Table 17: tasks_exceptions ────────────────────────────────────────────────

class TaskException(TimestampedBase):
    __tablename__ = "tasks_exceptions"

    exception_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("probate_cases.case_id"), nullable=False
    )
    failed_gate: Mapped[int] = mapped_column(Integer, nullable=False)  # Gate 1 to 6
    exception_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[ExceptionPriority] = mapped_column(
        String(50), default=ExceptionPriority.NORMAL, nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True, nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationship
    case: Mapped["ProbateCase"] = relationship("ProbateCase")


# ── Convenience alias for Alembic env.py ──────────────────────────────────────
__all__ = [
    "Base",
    "County", "Person", "ContactPoint",
    "ProbateCase", "Property", "PropertyAssessment",
    "Encumbrance", "TaxLien", "OwnershipAssessment",
    "ControlAssessment", "AuthorityAssessment",
    "Opportunity", "Client", "TerritoryAgreement",
    "OpportunityDelivery", "EvidenceRecord", "TaskException",
]
