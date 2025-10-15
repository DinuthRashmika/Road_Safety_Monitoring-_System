# app/deps.py
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.db.mongo import get_db
from app.security.jwt import decode_token


# ---------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------
async def get_database():
    """
    Provides the MongoDB database instance for dependency injection.
    Example:
        @router.get("/items")
        async def list_items(db = Depends(get_database)):
            docs = await db["items"].find().to_list(length=100)
            return docs
    """
    return get_db()


# ---------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    Decodes JWT from the Authorization header.
    Returns payload dict {sub, role, ...}.
    Raises 401 if token invalid or missing.
    """
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = creds.credentials
    try:
        payload = decode_token(token)
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def require_roles(*roles: str):
    """
    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])
        async def only_admin(): ...
    """
    async def _role_dep(payload: dict = Depends(get_current_user)):
        if payload.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return payload
    return _role_dep


# ---------------------------------------------------------------------
# Pagination helper (optional)
# ---------------------------------------------------------------------
def pagination_params(limit: int = 50, skip: int = 0) -> tuple[int, int]:
    """
    Standard pagination dependency. Clamp values for safety.
    Example:
        async def list_items(p: tuple = Depends(pagination_params)):
            limit, skip = p
    """
    limit = min(max(limit, 1), 200)
    skip = max(skip, 0)
    return limit, skip
