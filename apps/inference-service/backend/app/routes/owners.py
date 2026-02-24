from fastapi import APIRouter, Depends, HTTPException, Request
import app.db.mongodb as mongodb
from app.core.deps import get_current_owner
from app.schemas.user import OwnerOut, OwnerUpdateIn
from app.utils.images import make_public_url

router = APIRouter(prefix="/api/owners", tags=["Owners"])

@router.get("/me", response_model=OwnerOut)
async def get_me(request: Request, current=Depends(get_current_owner)):
    try:
        public_image = make_public_url(request, current.get("imageUrl"))
        return {
            "id": str(current["_id"]),
            "fullName": current["fullName"],
            "email": current["email"],
            "phone": current["phone"],
            "address": current["address"],
            "nic": current["nic"],
            "role": current["role"],
            "imageUrl": public_image,
        }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_me: {e}")
        raise HTTPException(500, f"Error getting user profile: {str(e)}")

@router.put("/me", response_model=OwnerOut)
async def update_me(request: Request, payload: OwnerUpdateIn, current=Depends(get_current_owner)):
    # Check if database is connected
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database not initialized")

    database = mongodb.db.db
    
    update = {}
    for field in ("fullName", "phone", "address"):
        val = getattr(payload, field)
        if val is not None:
            update[field] = val

    if not update:
        raise HTTPException(400, "Nothing to update")

    await database.users.update_one({"_id": current["_id"]}, {"$set": update})
    user = await database.users.find_one({"_id": current["_id"]})

    public_image = make_public_url(request, user.get("imageUrl"))
    return {
        "id": str(user["_id"]),
        "fullName": user["fullName"],
        "email": user["email"],
        "phone": user["phone"],
        "address": user["address"],
        "nic": user["nic"],
        "role": user["role"],
        "imageUrl": public_image,
    }