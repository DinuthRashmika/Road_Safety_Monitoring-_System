from __future__ import annotations
from typing import Optional, Dict, Any

from app.security.password import hash_password
from .repo import create_user, update_user
from .schemas import Location 

async def admin_create_user(name: str, email: str, role: str, password: str, location: Location) -> str:
    ph = hash_password(password)
    # Pass location as a dict
    return await create_user(name, email, role, ph, location.model_dump())

async def admin_update_user(user_id: str, fields: Dict[str, Any]) -> None:
    """
    fields may include: name, email, role, password, location
    If password is present, convert to password_hash.
    """
    patch: Dict[str, Any] = {}
    for k in ("name", "email", "role", "location"):
        if k in fields and fields[k] is not None:
            patch[k] = fields[k]
    if "password" in fields and fields["password"]:
        patch["password_hash"] = hash_password(fields["password"])
    if not patch:
        return
    await update_user(user_id, patch)