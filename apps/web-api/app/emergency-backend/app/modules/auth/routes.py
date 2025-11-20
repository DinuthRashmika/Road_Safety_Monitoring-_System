from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.security.password import verify_password
from app.security.jwt import create_access_token
from app.deps import get_current_responder_doc
from app.modules.responders.schemas import UserView

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    password = payload.password

    db = get_db()
    user = await db["users"].find_one({"email": email})
    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]), user.get("role"))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserView)
async def me(responder: dict = Depends(get_current_responder_doc)):
    """
    Get the full document for the currently authenticated responder.
    """
    return responder