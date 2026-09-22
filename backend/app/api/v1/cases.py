import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.property import ProbateCase
from app.models.jurisdiction import County
from app.workers.ingestion_worker import MunicipalIngestionWorker

router = APIRouter(prefix="/cases", tags=["Court Cases"])


class CaseResponse(BaseModel):
    case_id: uuid.UUID
    case_number: str
    filing_date: date
    county_fips: str
    decedent_name: str
    attorney_quarantined: bool
    invariant_hash: str


class IngestRequest(BaseModel):
    county_fips: str
    target_date: Optional[date] = None


@router.get("", response_model=List[CaseResponse])
def list_probate_cases(
    county_fips: Optional[str] = Query(None, min_length=5, max_length=5),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists ingested probate court cases across active county jurisdictions."""
    query = db.query(ProbateCase)
    if county_fips:
        query = query.join(ProbateCase.county).filter(County.county_fips == county_fips)

    cases = query.order_by(ProbateCase.filing_date.desc()).offset(skip).limit(limit).all()
    return [
        CaseResponse(
            case_id=c.case_id,
            case_number=c.case_number,
            filing_date=c.filing_date,
            county_fips=c.county.county_fips,
            decedent_name=f"{c.decedent.first_name} {c.decedent.last_name}",
            attorney_quarantined=c.attorney_quarantined,
            invariant_hash=c.invariant_hash
        ) for c in cases
    ]


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def trigger_county_ingest(payload: IngestRequest):
    """Executes the Playwright scraper worker to ingest court filings."""
    target_date = payload.target_date or date.today()
    worker = MunicipalIngestionWorker(county_fips=payload.county_fips)
    raw_dockets = await worker.scrape_portal(search_date=target_date)
    case_ids = worker.process_and_commit(raw_dockets)
    return {
        "status": "COMPLETED",
        "county_fips": payload.county_fips,
        "cases_ingested_count": len(case_ids),
        "case_ids": [str(cid) for cid in case_ids]
    }
