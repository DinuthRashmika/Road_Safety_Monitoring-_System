from pydantic import BaseModel, EmailStr
from typing import Literal, Optional

Role = Literal["admin", "police", "ambulance", "fire"]

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role
    password: str

class UserView(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role

class Unit(BaseModel):
    id: str | None = None
    code: str
    type: Literal["police", "ambulance", "fire"]
    home_lat: float
    home_lng: float
    status: Literal["available", "busy", "off"] = "available"
