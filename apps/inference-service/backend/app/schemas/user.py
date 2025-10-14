from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class OwnerRegisterIn(BaseModel):
    fullName: str = Field(..., min_length=2)
    email: EmailStr
    phone: str = Field(..., min_length=7)
    address: str
    nic: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)

class OwnerOut(BaseModel):
    id: str
    fullName: str
    email: EmailStr
    phone: str
    address: str
    nic: str
    role: str
    imageUrl: Optional[str] = None

class OwnerUpdateIn(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
