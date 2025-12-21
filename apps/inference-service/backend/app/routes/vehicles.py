from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from typing import Optional
from bson import ObjectId
import app.db.mongodb as mongodb
from app.core.deps import get_current_owner
from app.schemas.vehicle import VehicleOut
from app.models.vehicle_model import vehicle_doc
from app.utils.images import save_image, make_public_url
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])

def _normalize_images_for_response(request: Request, images: dict | None) -> dict:
    if not images:
        return {"front": None, "back": None, "right": None, "left": None, "plate": None}
    out = {}
    for k, v in images.items():
        out[k] = make_public_url(request, v)
    for k in ("front", "back", "right", "left", "plate"):
        out.setdefault(k, None)
    return out

@router.post("", response_model=VehicleOut, status_code=201)
async def create_vehicle(
    request: Request,
    current=Depends(get_current_owner),
    vehicleType: str = Form(...),
    vehicleModel: str = Form(...),
    registrationDate: str = Form(...),
    plateNo: str = Form(...),
    image_front: UploadFile | None = File(None),
    image_back: UploadFile | None = File(None),
    image_right: UploadFile | None = File(None),
    image_left: UploadFile | None = File(None),
    image_plate: UploadFile | None = File(None),
):
    # Check if database is connected
    if mongodb.db is None or mongodb.db.db is None:
        logger.error("Database not initialized in create_vehicle")
        raise HTTPException(500, "Database not initialized")

    database = mongodb.db.db
    
    # Check if vehicle with this plate already exists
    existing_vehicle = await database.vehicles.find_one({"plateNo": plateNo.upper()})
    if existing_vehicle:
        raise HTTPException(400, "Vehicle with this plate already exists")

    v_id = ObjectId()
    images: dict[str, Optional[str]] = {}
    subdir = f"vehicles/{str(current['_id'])}/{str(v_id)}"

    # Save images
    if image_front:
        images["front"] = await save_image(image_front, subdir=subdir)
    if image_back:
        images["back"] = await save_image(image_back, subdir=subdir)
    if image_right:
        images["right"] = await save_image(image_right, subdir=subdir)
    if image_left:
        images["left"] = await save_image(image_left, subdir=subdir)
    if image_plate:
        images["plate"] = await save_image(image_plate, subdir=subdir)

    # Create vehicle document
    doc = vehicle_doc(
        ownerId=current["_id"],
        vehicleType=vehicleType,
        vehicleModel=vehicleModel,
        registrationDate=registrationDate,
        plateNo=plateNo,
        images=images,
    )
    doc["_id"] = v_id
    
    # Insert into database
    await database.vehicles.insert_one(doc)

    # Prepare response
    images_out = _normalize_images_for_response(request, doc["images"])

    return {
        "id": str(doc["_id"]),
        "ownerId": str(doc["ownerId"]),
        "vehicleType": doc["vehicleType"],
        "vehicleModel": doc["vehicleModel"],
        "registrationDate": doc["registrationDate"],
        "plateNo": doc["plateNo"],
        "status": doc["status"],
        "images": images_out,
    }

@router.get("/mine", response_model=list[VehicleOut])
async def list_my_vehicles(request: Request, current=Depends(get_current_owner)):
    # Check if database is connected
    if mongodb.db is None or mongodb.db.db is None:
        logger.error("Database not initialized in list_my_vehicles")
        raise HTTPException(500, "Database not initialized")

    database = mongodb.db.db
    
    cursor = database.vehicles.find({"ownerId": current["_id"]})
    out = []
    async for v in cursor:
        out.append({
            "id": str(v["_id"]),
            "ownerId": str(v["ownerId"]),
            "vehicleType": v["vehicleType"],
            "vehicleModel": v["vehicleModel"],
            "registrationDate": v["registrationDate"],
            "plateNo": v["plateNo"],
            "status": v["status"],
            "images": _normalize_images_for_response(request, v.get("images", {})),
        })
    return out

@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: str, request: Request, current=Depends(get_current_owner)):
    # Check if database is connected
    if mongodb.db is None or mongodb.db.db is None:
        logger.error("Database not initialized in get_vehicle")
        raise HTTPException(500, "Database not initialized")

    database = mongodb.db.db
    
    v = await database.vehicles.find_one({"_id": ObjectId(vehicle_id), "ownerId": current["_id"]})
    if not v:
        raise HTTPException(404, "Vehicle not found")
    
    return {
        "id": str(v["_id"]),
        "ownerId": str(v["ownerId"]),
        "vehicleType": v["vehicleType"],
        "vehicleModel": v["vehicleModel"],
        "registrationDate": v["registrationDate"],
        "plateNo": v["plateNo"],
        "status": v["status"],
        "images": _normalize_images_for_response(request, v.get("images", {})),
    }