from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional # Make sure Optional is imported

# ----- Shared role/type enums -----
Role = Literal["admin", "police", "ambulance", "fire"]

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
    location: Location 

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    password: Optional[str] = None  
    location: Optional[Location] = None 

class UserView(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    location: Optional[Location] = None 