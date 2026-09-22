import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedBase
from app.models.enums import PropertyClass

if TYPE_CHECKING:
    from app.models.jurisdiction import County
    from app.models.identity import Person
    from app.models.intelligence import AuthorityAssessment, ControlAssessment, Opportunity, OwnershipAssessment


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


class Encumbrance(TimestampedBase):
    __tablename__ = "encumbrances"

    encumbrance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False
    )
    encumbrance_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Senior Mortgage, HELOC, etc.
    lender_name: Mapped[str] = mapped_column(String(200), nullable=False)
    original_recording_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    original_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    instrument_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    property: Mapped["Property"] = relationship("Property", back_populates="encumbrances")


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
