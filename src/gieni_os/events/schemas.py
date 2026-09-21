"""
Gieni OS Canonical Event Schemas
Dataclasses representing immutable data contracts between decoupled microservices.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time

@dataclass
class PropertyIdentifiedEvent:
    caseId: str
    propertyId: str
    apn: str
    situsAddress: Dict[str, Any]
    pasScore: float
    assessedValue: float = 0.0
    eventType: str = "Property.Identified"
    timestamp: float = field(default_factory=time.time)

@dataclass
class OwnershipUpdatedEvent:
    propertyId: str
    vestingType: str
    titleComplexityScore: int
    openMortgages: float
    netEquity: float
    deedInstrument: str = "AUD-RECORDING"
    eventType: str = "Ownership.Updated"
    timestamp: float = field(default_factory=time.time)

@dataclass
class ControlChangedEvent:
    propertyId: str
    decisionMakerName: Optional[str] = None
    relationship: Optional[str] = None
    controlArchetype: str = "Model 1: Unified Fiduciary Control"
    occupancyStatus: str = "vacant"
    residentCaretaker: bool = False
    eventType: str = "Control.Changed"
    timestamp: float = field(default_factory=time.time)

@dataclass
class AuthorityUpdatedEvent:
    propertyId: str
    authorityTier: str
    lettersStatus: str
    statutoryPowers: str
    courtOversight: str
    fiduciaryName: Optional[str] = None
    eventType: str = "Authority.Updated"
    timestamp: float = field(default_factory=time.time)

@dataclass
class OpportunityScoredEvent:
    opportunityId: str
    compositeViabilityScore: int
    dealFrictionScore: int
    priorityTier: str
    recommendedStrategy: str
    eventType: str = "Opportunity.Scored"
    timestamp: float = field(default_factory=time.time)

@dataclass
class EvidenceIngestedEvent:
    caseId: str
    docTitle: str
    sha256Hash: str
    eventType: str = "Evidence.Ingested"
    timestamp: float = field(default_factory=time.time)

@dataclass
class OpportunityQCCertifiedEvent:
    opportunityId: str
    certificationStatus: str
    confidenceScore: float
    gateResults: Dict[str, bool] = field(default_factory=dict)
    eventType: str = "Opportunity.QCCertified"
    timestamp: float = field(default_factory=time.time)

@dataclass
class OpportunityDeliveredEvent:
    opportunityId: str
    clientId: str
    webhookAck: bool
    deliveryLatencyMs: int
    deliveryChannel: str = "CRM_WEBHOOK"
    eventType: str = "Opportunity.Delivered"
    timestamp: float = field(default_factory=time.time)
    confidenceScore: float = 0.0
    gateResults: Dict[str, bool] = field(default_factory=dict)

@dataclass
class TelemetryIngestedEvent:
    opportunityId: str
    clientId: str
    dispositionStage: str
    contactOutcome: str
    decisionMakerAccurate: bool = True
    wholesaleFeeRealized: float = 0.0
    eventType: str = "Telemetry.Ingested"
    timestamp: float = field(default_factory=time.time)

@dataclass
class PipelineExceptionRoutedEvent:
    caseId: str
    exceptionCode: str
    assignedQueue: str
    reason: str
    eventType: str = "Pipeline.ExceptionRouted"
    timestamp: float = field(default_factory=time.time)
