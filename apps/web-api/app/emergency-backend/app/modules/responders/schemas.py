from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional 

Role = Literal["admin", "police", "ambulance", "fire"]

class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role
    password: str
    contact_number: Optional[str] = None    
    location: Location 

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    password: Optional[str] = None  
    contact_number: Optional[str] = None  
    location: Optional[Location] = None 

class UserView(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    contact_number: Optional[str] = None  
    location: Optional[Location] = None