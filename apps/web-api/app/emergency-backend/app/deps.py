from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from bson import ObjectId

from app.db.mongo import get_db
from app.security.jwt import decode_token
from app.modules.responders.repo import get_user

# Database dependency

async def get_database():
    return get_db()

# Authentication dependency

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = creds.credentials
    try:
        payload = decode_token(token)
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

async def get_current_responder_doc(payload: dict = Depends(get_current_user)) -> dict:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        
    user_doc = await get_user(user_id)
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Responder not found")
        
    return user_doc


def require_roles(*roles: str): 

    async def _role_dep(payload: dict = Depends(get_current_user)):
        if payload.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_4S_FORBIDDEN, detail="Forbidden")
        return payload
    return _role_dep