import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedBase
from app.models.enums import DeliveryChannel

if TYPE_CHECKING:
    from app.models.jurisdiction import County
    from app.models.intelligence import Opportunity


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
        UniqueConstraint("county_id", name="uq_single_partner_per_county"), # Enforces County Exclusivity
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="territory_agreements")
    county: Mapped["County"] = relationship("County", back_populates="territory_agreements")


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
    client: Mapped["Client"] = relationship("Client", back_populates="deliveries")
