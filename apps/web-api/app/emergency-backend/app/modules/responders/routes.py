from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from app.security.roles import require_roles
from .schemas import UserCreate, UserView, Unit
from .service import admin_create_user
from .repo import list_users, delete_user, create_unit, list_units, update_unit, delete_unit

router = APIRouter()

# ---------- Users ----------
@router.post("/responders", dependencies=[Depends(require_roles("admin"))])
async def create_responder(body: UserCreate):
    try:
        user_id = await admin_create_user(body.name, body.email, body.role, body.password)
        return {"id": user_id}
    except ValueError as e:
        if str(e) == "email_exists":
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        raise

@router.get("/responders", response_model=list[UserView], dependencies=[Depends(require_roles("admin"))])
async def get_responders():
    return await list_users()

@router.delete("/responders/{user_id}", dependencies=[Depends(require_roles("admin"))])
async def remove_responder(user_id: str):
    await delete_user(user_id)
    return {"ok": True}

# ---------- Units ----------
@router.post("/units", dependencies=[Depends(require_roles("admin"))])
async def create_unit_route(body: Unit):
    try:
        _id = await create_unit(body.model_dump(exclude_none=True))
        return {"id": _id}
    except ValueError as e:
        if str(e) == "unit_code_exists":
            raise HTTPException(status_code=409, detail="A unit with this code already exists")
        raise

@router.get("/units", dependencies=[Depends(require_roles("admin"))])
async def get_units():
    return await list_units()

@router.put("/units/{unit_id}", dependencies=[Depends(require_roles("admin"))])
async def edit_unit(unit_id: str, body: dict):
    await update_unit(unit_id, body)
    return {"ok": True}

@router.delete("/units/{unit_id}", dependencies=[Depends(require_roles("admin"))])
async def remove_unit(unit_id: str):
    await delete_unit(unit_id)
    return {"ok": True}
