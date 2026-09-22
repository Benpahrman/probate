from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PropertyClass


class PropertyCreate(BaseModel):
    case_id: UUID
    county_id: UUID
    apn: str
    street: str
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str
    legal_description: Optional[str] = None
    property_class: PropertyClass = PropertyClass.SINGLE_FAMILY
    pas_score: float = Field(..., ge=0.0, le=100.0)

    model_config = ConfigDict(from_attributes=True)


class PropertyResponse(PropertyCreate):
    property_id: UUID
    living_area_sqft: Optional[int] = None
    lot_size_acres: Optional[float] = None
    is_vacant: bool = False
