"""
Gieni OS Domain Layer
Pure business entities and value objects
"""

from gieni_os.domain.probate import DocketRecord, CaseStatus
from gieni_os.domain.property import SitusAddress, PropertyRecord
from gieni_os.domain.ownership import VestingType, EquityWaterfall, OwnershipRecord
from gieni_os.domain.authority import AuthorityTier, LettersType, FiduciaryAuthorityRecord
from gieni_os.domain.control import (
    ControlArchetype,
    OccupancyStatus,
    DecisionMaker,
    ControlProfile
)
from gieni_os.domain.contact import (
    LineType,
    PhoneRecord,
    ContactEnrichmentRecord
)
from gieni_os.domain.scoring import (
    PriorityTier,
    DealStrategy,
    DealFrictionScore,
    OpportunityScore
)
from gieni_os.domain.qc import (
    GateResult,
    QCValidationReport
)
from gieni_os.domain.delivery import (
    DeliveryChannel,
    CRMPlatform,
    FlashAlert,
    DeliveryDispatchRecord
)
from gieni_os.domain.telemetry import (
    DispositionStage,
    DispositionRecord,
    CountyCalibrationProfile
)
from gieni_os.domain.expansion import (
    ExpansionStatus,
    CountyFeasibility
)
