from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt import decode_token

bearer = HTTPBearer()

def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_roles(*roles: str):
    def dep(payload: dict = Depends(current_user)):
        if payload.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    return dep
