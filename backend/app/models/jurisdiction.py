import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.property import ProbateCase, Property
    from app.models.commercial import TerritoryAgreement


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
