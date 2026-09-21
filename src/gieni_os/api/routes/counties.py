"""
Counties API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from gieni_os.database.connection import get_db
from gieni_os.database.models import CountyModel
from gieni_os.api.deps import get_current_user

router = APIRouter(prefix="/counties", tags=["Counties"])

class CountyCreate(BaseModel):
    id: Optional[str] = None
    name: str
    state: str = "WA"
    status: str = "ACTIVE"
    tier: str = "TIER_1"

class CountyUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[str] = None

class CountyResponse(BaseModel):
    id: str
    name: str
    state: str
    status: str
    tier: str

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[CountyResponse])
def list_counties(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    return db.query(CountyModel).offset(offset).limit(limit).all()

@router.post("", response_model=CountyResponse, status_code=status.HTTP_201_CREATED)
def create_county(county_in: CountyCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    c_id = county_in.id or f"cty_{county_in.name.lower().replace(' ', '_')}"
    existing = db.query(CountyModel).filter(CountyModel.id == c_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="County ID already exists.")
    
    county = CountyModel(
        id=c_id,
        name=county_in.name,
        state=county_in.state,
        status=county_in.status,
        tier=county_in.tier
    )
    db.add(county)
    db.commit()
    db.refresh(county)
    return county

@router.put("/{county_id}", response_model=CountyResponse)
def update_county(county_id: str, county_in: CountyUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    county = db.query(CountyModel).filter(CountyModel.id == county_id).first()
    if not county:
        raise HTTPException(status_code=404, detail="County not found.")
    
    if county_in.name is not None:
        county.name = county_in.name
    if county_in.status is not None:
        county.status = county_in.status
    if county_in.tier is not None:
        county.tier = county_in.tier

    db.commit()
    db.refresh(county)
    return county
