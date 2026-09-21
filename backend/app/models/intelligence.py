import uuid
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import String, Boolean, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedBase
from app.models.enums import (
    LifecycleStage,
    PriorityTier,
    AuthorityTier,
    LettersStatus,
    PowerScope,
    ControlArchetype,
    VestingType
)

if TYPE_CHECKING:
    from app.models.property import ProbateCase, Property
    from app.models.identity import Person
    from app.models.commercial import OpportunityDelivery


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
    composite_viability_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 to 100
    deal_friction_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)        # 0 to 100
    priority_tier: Mapped[PriorityTier] = mapped_column(
        String(50), default=PriorityTier.DISQUALIFIED, index=True, nullable=False
    )
    dispatch_sla: Mapped[str] = mapped_column(String(50), default="STANDARD_BATCH", nullable=False)
    is_qc_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    case: Mapped["ProbateCase"] = relationship("ProbateCase", back_populates="opportunity")
    property: Mapped["Property"] = relationship("Property")
    deliveries: Mapped[List["OpportunityDelivery"]] = relationship("OpportunityDelivery", back_populates="opportunity")
