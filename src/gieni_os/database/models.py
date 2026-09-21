"""
SQLAlchemy ORM Models for Gieni OS Database Foundation
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, ForeignKey, Text, Boolean, Float
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def gen_uuid() -> str:
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class CountyModel(Base):
    __tablename__ = "counties"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    state = Column(String(32), nullable=False, default="WA")
    status = Column(String(32), nullable=False, default="ACTIVE")
    tier = Column(String(32), nullable=False, default="TIER_1")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    clients = relationship("ClientModel", back_populates="county")
    cases = relationship("ProbateCaseModel", back_populates="county")
    opportunities = relationship("OpportunityModel", back_populates="county")

class ClientModel(Base):
    __tablename__ = "clients"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    renewal_date = Column(Date, nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE")
    county_id = Column(String(64), ForeignKey("counties.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    county = relationship("CountyModel", back_populates="clients")

class ProbateCaseModel(Base):
    __tablename__ = "probate_cases"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    case_number = Column(String(64), unique=True, nullable=False)
    county_id = Column(String(64), ForeignKey("counties.id", ondelete="CASCADE"), nullable=False)
    decedent = Column(String(256), nullable=False)
    filing_date = Column(Date, nullable=False, default=date.today)
    status = Column(String(32), nullable=False, default="OPEN")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    county = relationship("CountyModel", back_populates="cases")
    opportunities = relationship("OpportunityModel", back_populates="case")

class OpportunityModel(Base):
    __tablename__ = "opportunities"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    case_id = Column(String(64), ForeignKey("probate_cases.id", ondelete="CASCADE"), nullable=False)
    county_id = Column(String(64), ForeignKey("counties.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_stage = Column(String(64), nullable=False, default="NEW", index=True)
    priority = Column(String(32), nullable=False, default="MEDIUM", index=True)
    authority_status = Column(String(64), nullable=False, default="UNRESOLVED")
    score = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    case = relationship("ProbateCaseModel", back_populates="opportunities")
    county = relationship("CountyModel", back_populates="opportunities")
    exceptions = relationship("ExceptionModel", back_populates="opportunity")
    audit_logs = relationship("WorkflowAuditLogModel", back_populates="opportunity")

class ExceptionModel(Base):
    __tablename__ = "exceptions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    opportunity_id = Column(String(64), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False, default="MEDIUM")
    status = Column(String(32), nullable=False, default="OPEN")
    assignee = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    opportunity = relationship("OpportunityModel", back_populates="exceptions")

class KnowledgeBaseModel(Base):
    __tablename__ = "knowledge_base"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    title = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    review_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

class WorkflowAuditLogModel(Base):
    __tablename__ = "workflow_audit_logs"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    opportunity_id = Column(String(64), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    from_stage = Column(String(64), nullable=False)
    to_stage = Column(String(64), nullable=False)
    transitioned_by = Column(String(128), nullable=False, default="System")
    timestamp = Column(DateTime, default=utc_now)
    notes = Column(Text, nullable=True)

    opportunity = relationship("OpportunityModel", back_populates="audit_logs")

class CRMDispatchLogModel(Base):
    __tablename__ = "crm_dispatch_logs"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    opportunity_id = Column(String(64), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    crm_platform = Column(String(64), nullable=False)
    webhook_url = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, default="DISPATCHED")
    response_code = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class TelemetryDispositionModel(Base):
    __tablename__ = "telemetry_dispositions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    opportunity_id = Column(String(64), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    client_name = Column(String(128), nullable=True)
    stage = Column(String(32), nullable=False)
    offer_amount = Column(Float, nullable=True)
    estimated_close_days = Column(Integer, nullable=True)
    dead_reason = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class AgentRegistryModel(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True)
    agent_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="OFFLINE")
    version = Column(String(32), nullable=False, default="1.0.0")
    capabilities = Column(Text, nullable=True)
    last_heartbeat = Column(DateTime, default=utc_now)


# =====================================================================
# Intelligence Context (The Brain) Database Models
# =====================================================================

class MemoryEntryModel(Base):
    __tablename__ = "memory_entries"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    scope = Column(String(32), nullable=False)  # CASE, OPPORTUNITY, COUNTY, ORGANIZATION, PLATFORM
    entity_id = Column(String(64), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.90)
    meta_json = Column(Text, nullable=True)  # Serialized attributes / state snapshot
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    observations = relationship("MemoryObservationModel", back_populates="entry", cascade="all, delete-orphan")


class MemoryObservationModel(Base):
    __tablename__ = "memory_observations"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    entry_id = Column(String(64), ForeignKey("memory_entries.id", ondelete="CASCADE"), nullable=False)
    observation = Column(Text, nullable=False)
    source = Column(String(64), nullable=False, default="ENGINE")  # ENGINE, AGENT, OPERATOR, COURT_RECORD
    confidence = Column(Float, nullable=False, default=0.90)
    created_at = Column(DateTime, default=utc_now)

    entry = relationship("MemoryEntryModel", back_populates="observations")


class KnowledgeArticleModel(Base):
    __tablename__ = "knowledge_articles"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    category = Column(String(64), nullable=False, index=True)  # COUNTY_RULES, SOP, ATTORNEY_PATTERN, TITLE_PATTERN, AUTHORITY_PATTERN
    title = Column(String(256), nullable=False)
    county_id = Column(String(64), nullable=True, index=True)
    content = Column(Text, nullable=False)
    statutory_reference = Column(String(128), nullable=True)  # e.g., RCW 11.68.011
    version = Column(String(16), nullable=False, default="1.0.0")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class LearningEventModel(Base):
    __tablename__ = "learning_events"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    opportunity_id = Column(String(64), nullable=False, index=True)
    county_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # OFFER, CONTRACT, DEAD_DEAL, NO_RESPONSE, CLOSING
    realized_margin = Column(Float, nullable=True)
    delta_score = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class CountyCalibrationModel(Base):
    __tablename__ = "county_calibrations"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    county_name = Column(String(128), unique=True, nullable=False)
    friction_index = Column(Float, nullable=False, default=1.0)
    avg_docket_days = Column(Integer, nullable=False, default=45)
    nonintervention_rate = Column(Float, nullable=False, default=0.85)
    last_calibrated = Column(DateTime, default=utc_now)


class VectorEmbeddingModel(Base):
    __tablename__ = "vector_embeddings"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    entity_type = Column(String(64), nullable=False, index=True)  # POF, CASE, KNOWLEDGE, ATTORNEY, COUNTY
    entity_id = Column(String(64), nullable=False, index=True)
    embedding_json = Column(Text, nullable=False)  # Serialized float vector
    dimension = Column(Integer, nullable=False, default=384)
    content_snippet = Column(Text, nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
