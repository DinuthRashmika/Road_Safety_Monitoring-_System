from fastapi import APIRouter, Depends, HTTPException
import app.db.mongodb as mongodb  # <-- use module
from app.core.deps import get_current_owner
from app.schemas.user import OwnerOut, OwnerUpdateIn

router = APIRouter(prefix="/api/owners", tags=["Owners"])

@router.get("/me", response_model=OwnerOut)
async def get_me(current=Depends(get_current_owner)):
    return {
        "id": str(current["_id"]),
        "fullName": current["fullName"],
        "email": current["email"],
        "phone": current["phone"],
        "address": current["address"],
        "nic": current["nic"],
        "role": current["role"],
        "imageUrl": current.get("imageUrl"),
    }

@router.put("/me", response_model=OwnerOut)
async def update_me(payload: OwnerUpdateIn, current=Depends(get_current_owner)):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    update = {}
    for field in ("fullName", "phone", "address"):
        val = getattr(payload, field)
        if val is not None:
            update[field] = val
    if not update:
        raise HTTPException(400, "Nothing to update")

    await mongodb.db.users.update_one({"_id": current["_id"]}, {"$set": update})
    user = await mongodb.db.users.find_one({"_id": current["_id"]})
    return {
        "id": str(user["_id"]),
        "fullName": user["fullName"],
        "email": user["email"],
        "phone": user["phone"],
        "address": user["address"],
        "nic": user["nic"],
        "role": user["role"],
        "imageUrl": user.get("imageUrl"),
    }
