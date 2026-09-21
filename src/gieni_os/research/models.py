"""
Gieni OS Research Models & Data Contracts
Modular definitions for Contacts/Skip-Trace, Title & Liens, Authority, and Valuation.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, ConfigDict

class ResearchArea(str, Enum):
    CONTACTS = "CONTACTS"
    TITLE = "TITLE"
    AUTHORITY = "AUTHORITY"
    VALUATION = "VALUATION"
    COMPREHENSIVE = "COMPREHENSIVE"

class PhoneContact(BaseModel):
    number: str
    line_type: str = "WIRELESS"  # WIRELESS, LANDLINE, VOIP
    carrier: Optional[str] = None
    confidence_score: float = 0.90
    is_dnc: bool = False
    is_primary: bool = False

class RelativeContact(BaseModel):
    name: str
    relationship: str
    phone: Optional[str] = None
    city_state: Optional[str] = None

class ContactResearchData(BaseModel):
    target_name: str
    relationship: str
    primary_phone: Optional[str] = None
    phones: List[PhoneContact] = Field(default_factory=list)
    verified_email: Optional[str] = None
    mailing_address: Optional[str] = None
    situs_address: Optional[str] = None
    situs_is_mailing: bool = False
    skip_trace_confidence: float = 92.0
    dnc_scrubbed: bool = True
    relatives_and_heirs: List[RelativeContact] = Field(default_factory=list)
    recommended_outreach_channel: str = "PHONE_CALL"
    outreach_script_template: Optional[str] = None

class DeedRecord(BaseModel):
    instrument_number: str
    recording_date: str
    deed_type: str  # STATUTORY_WARRANTY, QUITCLAIM, LACK_OF_PROBATE, TODD
    grantor: str
    grantee: str
    book_page: Optional[str] = None
    notes: Optional[str] = None

class LienRecord(BaseModel):
    lien_type: str  # MORTGAGE, HELOC, MECHANICS, TAX_DELINQUENT, HOA
    recording_number: str
    original_amount: float
    estimated_balance: float
    recording_date: str
    creditor_name: str
    status: str = "ACTIVE"

class TitleResearchData(BaseModel):
    apn: str
    county: str
    situs_address: str
    legal_description: str
    assessed_value: float
    land_value: float
    improvement_value: float
    tax_status: str = "CURRENT"
    vesting_type: str
    title_complexity_score: int = 15
    deed_chain: List[DeedRecord] = Field(default_factory=list)
    open_encumbrances: List[LienRecord] = Field(default_factory=list)
    total_senior_debt: float = 0.0
    total_junior_debt: float = 0.0
    has_title_cloud: bool = False
    title_cloud_flags: List[str] = Field(default_factory=list)
    curative_actions: List[str] = Field(default_factory=list)

class AuthorityResearchData(BaseModel):
    """
    Verified probate court docket and statutory authority findings under Washington RCW Title 11.
    """
    case_number: str = Field(..., description="Probate cause number or court docket identifier")
    county: str = Field(..., description="Jurisdiction superior court name")
    decedent: Optional[str] = Field(None, description="Legal decedent name from court docket")
    filing_date: Optional[str] = Field(None, description="Date petition was recorded with Superior Court clerk")
    authority_tier: str = Field("Tier 1: Court Certified", description="Gieni statutory authority tier (Tier 1-4)")
    letters_type: str = Field("Letters Testamentary", description="Classification of letters issued (Testamentary, Administration, None)")
    nonintervention_powers: bool = Field(True, description="Whether personal representative was granted autonomous RCW 11.68 powers")
    can_execute_psa: bool = Field(True, description="Whether fiduciary possesses independent legal capacity to execute real estate purchase agreement")
    court_confirmation_required: bool = Field(False, description="Whether judicial sale confirmation under RCW 11.76 is required before deed recording")
    statutory_basis: str = Field("RCW 11.68.011", description="Statutory authority citation under Washington law")
    fiduciary_name: Optional[str] = Field(None, description="Court-appointed fiduciary or petitioner name, or None if unappointed")
    fiduciary_relationship: Optional[str] = Field(None, description="Statutory capacity or family relationship to decedent")
    attorney_name: Optional[str] = Field(None, description="Estate legal counsel of record, or None if pro-se")
    notice_to_creditors_published: bool = Field(True, description="Whether Notice to Creditors has been filed and published")
    creditor_claim_window_status: str = Field("RUNNING_120_DAYS", description="Status of the 4-month creditor claim window (RCW 11.40.020)")
    legal_summary: str = Field(..., description="Concise legal analysis of contracting power and closing conditions")

class ValuationResearchData(BaseModel):
    """
    Automated Valuation Model (AVM) assessment, equity waterfall, and wholesale MAO calculations.
    """
    estimated_market_value: float = Field(..., description="As-is or after-repair market valuation (ARV)")
    assessed_value: float = Field(..., description="County tax assessor certified roll valuation")
    comps_median: float = Field(..., description="Median sales comp price in immediate submarket")
    estimated_repairs: float = Field(0.0, description="Estimated deferred maintenance deductions")
    closing_costs: float = Field(0.0, description="Estimated title, escrow, excise tax, and transfer fees")
    net_distributable_equity: float = Field(..., description="Distributable net proceeds after senior debt, repairs, and fees")
    target_wholesale_mao: float = Field(..., description="Maximum Allowable Offer for acquisition partners based on 70% rule")
    equity_spread_ratio: float = Field(0.0, description="Ratio of distributable equity to market value")
    deal_friction_score: int = Field(0, description="Deal friction and leverage index (0-100)")

class ResearchDossier(BaseModel):
    """
    Canonical 360-degree investigative research package consolidating contacts, title, authority, and valuation.
    """
    opportunity_id: Optional[str] = Field(None, description="Unique opportunity identifier linked to database")
    research_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="UTC timestamp of dossier assembly")
    area: ResearchArea = Field(..., description="Research scope completed")
    overall_confidence: float = Field(0.94, description="Investigative confidence score (0.0 - 1.0)")
    summary_notes: str = Field(..., description="Executive briefing on opportunity title, fiduciary, and economics")
    contacts: Optional[ContactResearchData] = Field(None, description="Skip-trace contact details for personal representative and heirs")
    title: Optional[TitleResearchData] = Field(None, description="Auditor deed chain, open encumbrances, and cloud status")
    authority: Optional[AuthorityResearchData] = Field(None, description="Judicial docket verification and signatory authority powers")
    valuation: Optional[ValuationResearchData] = Field(None, description="AVM valuation, net equity waterfall, and wholesale MAO")

    model_config = ConfigDict(from_attributes=True)

class ResearchRequest(BaseModel):
    """
    Input request specification for triggering single or comprehensive research sweeps.
    """
    opportunity_id: Optional[str] = Field(None, description="Opportunity ID to pull database context from")
    area: ResearchArea = Field(ResearchArea.COMPREHENSIVE, description="Specific research area or full comprehensive sweep")
    target_name: Optional[str] = Field(None, description="Subject individual name (e.g. personal representative or decedent)")
    address: Optional[str] = Field(None, description="Property situs address for parcel lookups")
    apn: Optional[str] = Field(None, description="County Assessor Parcel Number")
    county_id: Optional[str] = Field("cty_pierce", description="County jurisdiction code")
    case_number: Optional[str] = Field(None, description="Superior court probate cause number")
    raw_phones: Optional[List[str]] = Field(None, description="Known phone numbers to verify and enrich")
    force_live: bool = Field(False, description="Whether to bypass provider cache and execute live public record scrapers")

class ProviderInfo(BaseModel):
    """
    Metadata describing an extensible research provider plug-in.
    """
    provider_id: str = Field(..., description="Unique provider registration slug")
    name: str = Field(..., description="Human-readable provider name")
    version: str = Field(..., description="Semantic version string")
    supported_areas: List[ResearchArea] = Field(..., description="List of ResearchArea domains handled by this provider")
    description: str = Field(..., description="Provider capabilities and data sources description")
    status: str = Field("ACTIVE", description="Provider availability status")
