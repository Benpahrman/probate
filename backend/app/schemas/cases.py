from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProbateCaseCreate(BaseModel):
    county_fips: str = Field(..., min_length=5, max_length=5)
    case_number: str = Field(..., min_length=3, max_length=100)
    filing_date: date
    decedent_first_name: str
    decedent_last_name: str
    date_of_death: Optional[date] = None
    petitioner_first_name: Optional[str] = None
    petitioner_last_name: Optional[str] = None
    attorney_name: Optional[str] = None
    raw_docket_url: Optional[str] = None
    invariant_hash: str = Field(..., min_length=64, max_length=64)

    model_config = ConfigDict(from_attributes=True)


class ProbateCaseResponse(ProbateCaseCreate):
    case_id: UUID
    county_id: UUID
    decedent_id: UUID
    petitioner_id: Optional[UUID] = None
    attorney_quarantined: bool = True
