"""
Probate Cases API Routes
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from gieni_os.database.connection import get_db
from gieni_os.database.models import ProbateCaseModel, CountyModel
from gieni_os.api.deps import get_current_user, ClerkUserContext

router = APIRouter(prefix="/cases", tags=["Probate Cases"])

class CaseCreate(BaseModel):
    id: Optional[str] = None
    case_number: str
    county_id: str
    decedent: str
    filing_date: Optional[date] = None
    status: str = "OPEN"

class CaseResponse(BaseModel):
    id: str
    case_number: str
    county_id: str
    decedent: str
    filing_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[CaseResponse])
def list_cases(
    county_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    query = db.query(ProbateCaseModel)
    if not user.is_internal_operator and user.contracted_county:
        query = query.filter(
            (ProbateCaseModel.county_id == user.contracted_county) |
            (ProbateCaseModel.county.has(CountyModel.name == user.contracted_county))
        )
    elif county_id:
        query = query.filter(ProbateCaseModel.county_id == county_id)
    return query.offset(offset).limit(limit).all()

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    # Verify county exists
    county = db.query(CountyModel).filter(CountyModel.id == case_in.county_id).first()
    if not county:
        raise HTTPException(status_code=404, detail=f"County '{case_in.county_id}' not found.")

    # Check case number uniqueness
    existing = db.query(ProbateCaseModel).filter(ProbateCaseModel.case_number == case_in.case_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Case number '{case_in.case_number}' already exists.")

    case = ProbateCaseModel(
        id=case_in.id,
        case_number=case_in.case_number,
        county_id=case_in.county_id,
        decedent=case_in.decedent,
        filing_date=case_in.filing_date or date.today(),
        status=case_in.status
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case
