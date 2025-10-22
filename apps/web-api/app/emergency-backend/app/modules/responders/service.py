from __future__ import annotations
from typing import Optional, Dict, Any

from app.security.password import hash_password
from .repo import create_user, update_user

async def admin_create_user(name: str, email: str, role: str, password: str) -> str:
    ph = hash_password(password)
    return await create_user(name, email, role, ph)

async def admin_update_user(user_id: str, fields: Dict[str, Any]) -> None:
    """
    fields may include: name, email, role, password
    If password is present, convert to password_hash.
    """
    patch: Dict[str, Any] = {}
    for k in ("name", "email", "role"):
        if k in fields and fields[k] is not None:
            patch[k] = fields[k]
    if "password" in fields and fields["password"]:
        patch["password_hash"] = hash_password(fields["password"])
    if not patch:
        return
    await update_user(user_id, patch)
