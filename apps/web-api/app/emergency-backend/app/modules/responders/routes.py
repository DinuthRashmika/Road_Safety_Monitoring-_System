from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from app.security.roles import require_roles
from .schemas import (
    UserCreate, UserUpdate, UserView,
    # Unit, UnitUpdate  <- REMOVED
)
from .service import admin_create_user, admin_update_user
from .repo import (
    list_users, get_user, delete_user,
    # create_unit, list_units, get_unit, update_unit, delete_unit <- REMOVED
)

router = APIRouter()

# =========================
# Responders (Users) – Admin only
# =========================
@router.post("/responders", dependencies=[Depends(require_roles("admin"))])
async def create_responder(body: UserCreate):
    try:
        user_id = await admin_create_user(
            body.name, body.email, body.role, body.password, body.location
        )
        return {"id": user_id}
    except ValueError as e:
        if str(e) == "email_exists":
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        raise

@router.get("/responders", response_model=list[UserView], dependencies=[Depends(require_roles("admin"))])
async def get_responders():
    return await list_users()

@router.get("/responders/{user_id}", response_model=UserView, dependencies=[Depends(require_roles("admin"))])
async def get_responder(user_id: str):
    u = await get_user(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Responder not found")
    return u  # matches UserView

@router.put("/responders/{user_id}", dependencies=[Depends(require_roles("admin"))])
async def edit_responder(user_id: str, body: UserUpdate):
    try:
        await admin_update_user(user_id, body.model_dump(exclude_none=True))
        return {"ok": True}
    except ValueError as e:
        if str(e) == "email_exists":
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        raise

@router.delete("/responders/{user_id}", dependencies=[Depends(require_roles("admin"))])
async def remove_responder(user_id: str):
    await delete_user(user_id)
    return {"ok": True}

# =========================
# Units – Admin only (ALL REMOVED)
# =========================