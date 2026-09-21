"""
Clients API Routes
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from gieni_os.database.connection import get_db
from gieni_os.database.models import ClientModel, CountyModel
from gieni_os.api.deps import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])

class ClientCreate(BaseModel):
    id: Optional[str] = None
    name: str
    renewal_date: date
    status: str = "ACTIVE"
    county_id: Optional[str] = None

class ClientResponse(BaseModel):
    id: str
    name: str
    renewal_date: date
    status: str
    county_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[ClientResponse])
def list_clients(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    return db.query(ClientModel).offset(offset).limit(limit).all()

@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client_in: ClientCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if client_in.county_id:
        county = db.query(CountyModel).filter(CountyModel.id == client_in.county_id).first()
        if not county:
            raise HTTPException(status_code=404, detail="County not found.")
            
    client = ClientModel(
        id=client_in.id,
        name=client_in.name,
        renewal_date=client_in.renewal_date,
        status=client_in.status,
        county_id=client_in.county_id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client
