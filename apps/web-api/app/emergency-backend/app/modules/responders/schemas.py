from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional

# ----- Shared role/type enums -----
Role = Literal["admin", "police", "ambulance", "fire"]
UnitType = Literal["police", "ambulance", "fire"]
UnitStatus = Literal["available", "busy", "off"]

# ----- Users (Responders) -----
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    password: Optional[str] = None  # optional; only set if changing password

class UserView(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role

# ----- Units -----
class Unit(BaseModel):
    id: str | None = None
    code: str
    type: UnitType
    home_lat: float
    home_lng: float
    status: UnitStatus = "available"

class UnitUpdate(BaseModel):
    code: Optional[str] = None
    type: Optional[UnitType] = None
    home_lat: Optional[float] = None
    home_lng: Optional[float] = None
    status: Optional[UnitStatus] = None
