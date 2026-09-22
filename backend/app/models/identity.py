import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import date
from sqlalchemy import String, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.property import ProbateCase


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
