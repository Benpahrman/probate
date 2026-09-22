import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedBase
from app.models.enums import ExceptionPriority

if TYPE_CHECKING:
    from app.models.property import ProbateCase


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
    priority: Mapped[ExceptionPriority] = mapped_column(String(50), default=ExceptionPriority.NORMAL, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True, nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationship
    case: Mapped["ProbateCase"] = relationship("ProbateCase")
