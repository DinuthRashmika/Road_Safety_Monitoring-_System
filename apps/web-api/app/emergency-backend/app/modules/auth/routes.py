from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.security.password import verify_password
from app.security.jwt import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    # Normalize email to match how we store it (lowercased, trimmed)
    email = payload.email.strip().lower()
    password = payload.password

    db = get_db()
    user = await db["users"].find_one({"email": email})
    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]), user.get("role", "responder"))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me():
    # Minimal placeholder; UI may store name/role from login or call
    # a protected /responders/me later if you add one.
    return {"ok": True}
