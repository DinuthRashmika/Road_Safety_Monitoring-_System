from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional

# ----- Shared role/type enums -----
Role = Literal["admin", "police", "ambulance", "fire"]
# UnitType = Literal["police", "ambulance", "fire"]  <- REMOVED
# UnitStatus = Literal["available", "busy", "off"]  <- REMOVED

# ----- Location (re-used by Responders and Incidents) -----
class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None

# ----- Users (Responders) -----
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role
    password: str
    location: Location # <-- ADDED

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    password: Optional[str] = None  # optional; only set if changing password
    location: Optional[Location] = None # <-- ADDED

class UserView(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    location: Location # <-- ADDED

# ----- Units ----- (ALL REMOVED)