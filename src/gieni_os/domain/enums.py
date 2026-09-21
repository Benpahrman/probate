"""
Gieni OS Canonical Enums
Single source of truth for all lifecycle stages, priority tiers, authority
tiers, and domain classification flags used by the FSM, Gatekeeper, engines,
and the test suite.

Transplanted from backend/app/models/enums.py and extended with any values
present in the legacy src/gieni_os domain layer.
"""

from enum import Enum


class LifecycleStage(str, Enum):
    """The canonical 14-stage OLE lifecycle state machine (15 values including ARCHIVED)."""
    DISCOVERED = "DISCOVERED"
    PROPERTY_IDENTIFIED = "PROPERTY_IDENTIFIED"
    OWNERSHIP_RESOLVED = "OWNERSHIP_RESOLVED"
    CONTROL_MAPPED = "CONTROL_MAPPED"
    AUTHORITY_RESOLVED = "AUTHORITY_RESOLVED"
    SCORED = "SCORED"
    QC_CERTIFIED = "QC_CERTIFIED"
    DELIVERED = "DELIVERED"
    CONTACTED = "CONTACTED"
    APPOINTMENT = "APPOINTMENT"
    OFFER = "OFFER"
    CONTRACT = "CONTRACT"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"
    ARCHIVED = "ARCHIVED"


class PriorityTier(str, Enum):
    PRIORITY_A = "PRIORITY_A"          # Score >= 80, <4h flash dispatch SLA
    PRIORITY_B = "PRIORITY_B"          # Score 60-79, weekly batch staging
    PRIORITY_C = "PRIORITY_C"          # Score 40-59, docket milestone watch
    DISQUALIFIED = "DISQUALIFIED"      # Score < 40 or fatal title cloud


class AuthorityTier(str, Enum):
    TIER_1_CONFIRMED = "TIER_1_CONFIRMED"                          # Letters Issued with Independent Powers
    TIER_2_LIKELY = "TIER_2_LIKELY"                                # Nominated in Will / Uncontested Petitioner
    TIER_3_STAKEHOLDER_CONSENSUS = "TIER_3_STAKEHOLDER_CONSENSUS"  # Intestate Multi-Heir Co-Tenancy
    TIER_4_UNRESOLVED = "TIER_4_UNRESOLVED"                        # Contested Petitions / Active Caveat


class LettersStatus(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"


class PowerScope(str, Enum):
    FULL_INDEPENDENT_ADMINISTRATION = "FULL_INDEPENDENT_ADMINISTRATION"
    DEPENDENT_COURT_SUPERVISED = "DEPENDENT_COURT_SUPERVISED"
    TRUST_DISPOSITION_POWERS = "TRUST_DISPOSITION_POWERS"
    UNAUTHORIZED = "UNAUTHORIZED"


class ControlArchetype(str, Enum):
    UNIFIED_FIDUCIARY = "UNIFIED_FIDUCIARY"
    INFORMAL_FAMILY_LEADER = "INFORMAL_FAMILY_LEADER"
    PROXY_CONTROLLER = "PROXY_CONTROLLER"
    TRUST_FIDUCIARY = "TRUST_FIDUCIARY"
    CONTESTED_FACTIONS = "CONTESTED_FACTIONS"


class VestingType(str, Enum):
    SOLE_FEE_SIMPLE = "SOLE_FEE_SIMPLE"
    JTWROS = "JTWROS"
    TENANCY_IN_COMMON = "TENANCY_IN_COMMON"
    REVOCABLE_LIVING_TRUST = "REVOCABLE_LIVING_TRUST"
    HEIR_PROPERTY = "HEIR_PROPERTY"
    ENTITY_OWNERSHIP = "ENTITY_OWNERSHIP"


class PropertyClass(str, Enum):
    SINGLE_FAMILY = "SINGLE_FAMILY"
    MULTI_FAMILY = "MULTI_FAMILY"
    VACANT_LAND = "VACANT_LAND"
    COMMERCIAL = "COMMERCIAL"


class DeliveryChannel(str, Enum):
    CRM_WEBHOOK = "CRM_WEBHOOK"
    SMS_FLASH_ALERT = "SMS_FLASH_ALERT"
    NOTION_SYNC = "NOTION_SYNC"
    PDF_DOSSIER = "PDF_DOSSIER"


class ExceptionPriority(str, Enum):
    CRITICAL = "CRITICAL"    # Net equity > $200k, 4-hour SLA
    HIGH = "HIGH"            # Net equity $100k-$200k, 24-hour SLA
    NORMAL = "NORMAL"        # Net equity < $100k, 24-hour SLA
