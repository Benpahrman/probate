"""
Gieni OS Ingestion Models & Data Contracts
Defines schemas for probate and non-probate court dockets, auditor recordings,
and published legal notices.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, ConfigDict

class HarvesterUnavailableError(Exception):
    """Raised when an automated scraper/harvester is unavailable or demo mode is disabled in production."""
    pass

class FilingChannel(str, Enum):
    SUPERIOR_COURT_DOCKET = "SUPERIOR_COURT_DOCKET"
    NOTICE_TO_CREDITORS = "NOTICE_TO_CREDITORS"
    AUDITOR_NON_PROBATE = "AUDITOR_NON_PROBATE"
    ODYSSEY_JIS = "ODYSSEY_JIS"

class ScrapedDocket(BaseModel):
    case_number: str
    decedent: str
    county_id: str
    channel: FilingChannel = FilingChannel.SUPERIOR_COURT_DOCKET
    filing_date: Optional[date] = None
    petitioner_name: Optional[str] = None
    petitioner_relationship: Optional[str] = None
    attorney_name: Optional[str] = None
    instrument_number: Optional[str] = None  # Auditor recording number (e.g. LOPA or TODD)
    property_hint: Optional[str] = None      # Street address or APN mentioned in petition/affidavit
    raw_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class HarvestRequest(BaseModel):
    county_id: str
    channel: FilingChannel = FilingChannel.SUPERIOR_COURT_DOCKET
    days_back: int = 7
    force_simulated: bool = False

class BulkImportRequest(BaseModel):
    county_id: str
    channel: FilingChannel = FilingChannel.SUPERIOR_COURT_DOCKET
    raw_text: Optional[str] = None
    dockets: Optional[List[ScrapedDocket]] = None

class IngestionSummary(BaseModel):
    channel: str
    county_id: str
    total_found: int
    cases_ingested: int
    opportunities_created: int
    duplicates_skipped: int
    sample_dockets: List[ScrapedDocket] = []
