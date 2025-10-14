from pydantic import BaseModel, Field
from typing import Optional, Dict

class VehicleCreateIn(BaseModel):
    vehicleType: str
    vehicleModel: str
    registrationDate: str  # YYYY-MM-DD
    plateNo: str = Field(..., min_length=3)

class VehicleOut(BaseModel):
    id: str
    ownerId: str
    vehicleType: str
    vehicleModel: str
    registrationDate: str
    plateNo: str
    images: Dict[str, Optional[str]]
