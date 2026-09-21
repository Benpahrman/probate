"""
Gieni OS Relational Data Models
Pydantic/Dataclass entities defining the 12 core relational tables from Sprint 2.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import datetime

class CourtSystemType(Enum):
    LINX = "LINX"
    ODYSSEY = "ODYSSEY"
    ECR = "ECR"
    TYLER = "TYLER"

class ExclusivityStatus(Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED_FOUNDING = "LOCKED_FOUNDING"
    LOCKED_GROWTH = "LOCKED_GROWTH"

class PropertyClass(Enum):
    SFR = "SFR"
    DUPLEX = "DUPLEX"
    TRIPLEX = "TRIPLEX"
    FOURPLEX = "FOURPLEX"
    VACANT_LAND = "VACANT_LAND"

class TitleVestingType(Enum):
    SOLE_FEE_SIMPLE = "SOLE_FEE_SIMPLE"
    JTWROS = "JTWROS"
    TENANCY_IN_COMMON = "TENANCY_IN_COMMON"
    COMMUNITY_PROPERTY = "COMMUNITY_PROPERTY"
    LIVING_TRUST = "LIVING_TRUST"

class AuthorityTier(Enum):
    TIER_1_COURT_CERTIFIED = "TIER_1_COURT_CERTIFIED"
    TIER_2_PROBABLE_FIDUCIARY = "TIER_2_PROBABLE_FIDUCIARY"
    TIER_3_NON_PROBATE_TRUST = "TIER_3_NON_PROBATE_TRUST"
    TIER_4_UNCERTAIN_UNPROBATED = "TIER_4_UNCERTAIN_UNPROBATED"

class PriorityTier(Enum):
    PRIORITY_A_FLASH = "PRIORITY_A_FLASH"
    PRIORITY_B_WEEKLY = "PRIORITY_B_WEEKLY"
    PRIORITY_C_MONITOR = "PRIORITY_C_MONITOR"
    DISQUALIFIED = "DISQUALIFIED"

@dataclass
class County:
    county_fips: str
    county_name: str
    state: str
    court_system_type: CourtSystemType
    scraping_cadence: str = "DAILY"
    exclusivity_status: ExclusivityStatus = ExclusivityStatus.AVAILABLE
    active_partner_id: Optional[str] = None

@dataclass
class ProbateCase:
    case_id: str
    county_fips: str
    docket_number: str
    filing_date: str
    case_status: str
    decedent_person_id: str
    case_type: str = "TESTATE"

@dataclass
class Property:
    property_id: str
    apn: str
    county_fips: str
    street_address: str
    city: str
    zip_code: str
    property_type: PropertyClass
    assessed_value: float
    avm_value: float
    gis_lat: Optional[float] = None
    gis_lng: Optional[float] = None
    zoning_code: Optional[str] = None

@dataclass
class Person:
    person_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_death: Optional[str] = None
    phone_primary: Optional[str] = None
    mailing_address: Optional[str] = None

@dataclass
class Stakeholder:
    stakeholder_id: str
    estate_id: str
    person_id: str
    relationship_to_decedent: str
    claim_percentage: float = 0.0

@dataclass
class Trust:
    trust_id: str
    trust_name: str
    formation_date: Optional[str] = None
    revocability: str = "REVOCABLE"
    current_trustee_id: Optional[str] = None

@dataclass
class Estate:
    estate_id: str
    probate_case_id: str
    gross_inventory_value: float = 0.0
    court_oversight_level: str = "NONINTERVENTION"
    insolvency_risk: bool = False

@dataclass
class AuthorityCandidate:
    candidate_id: str
    estate_id: str
    person_id: str
    authority_role: str
    letters_issued: bool
    powers_granted: str
    statutory_source: str = "RCW 11.68.011"

@dataclass
class Opportunity:
    opportunity_id: str
    property_id: str
    estate_id: str
    authority_candidate_id: str
    composite_score: int
    priority_tier: PriorityTier
    net_equity_spread: float
    deal_friction_score: int
    assigned_partner_id: Optional[str] = None
    qc_pass_date: Optional[str] = None

@dataclass
class EvidenceSource:
    evidence_id: str
    opportunity_id: str
    source_type: str
    source_reference_id: str
    verification_hash: str

@dataclass
class Client:
    client_id: str
    company_name: str
    primary_contact: str
    partner_tier: str
    assigned_county_fips: str
    webhook_url: str
    monthly_file_allocation: int

@dataclass
class Disposition:
    disposition_id: str
    opportunity_id: str
    client_id: str
    disposition_stage: str
    wholesale_fee: Optional[float] = None
    days_to_contact: Optional[int] = None
    loss_reason: Optional[str] = None
