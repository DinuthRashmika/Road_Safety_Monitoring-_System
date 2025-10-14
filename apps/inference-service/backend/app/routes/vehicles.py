from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from bson import ObjectId
import app.db.mongodb as mongodb  # <-- use module
from app.core.deps import get_current_owner
from app.schemas.vehicle import VehicleOut
from app.models.vehicle_model import vehicle_doc
from app.utils.images import save_image

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])

@router.post("", response_model=VehicleOut, status_code=201)
async def create_vehicle(
    current=Depends(get_current_owner),
    vehicleType: str = Form(...),
    vehicleModel: str = Form(...),
    registrationDate: str = Form(...),  # YYYY-MM-DD
    plateNo: str = Form(...),
    image_front: UploadFile | None = File(None),
    image_back: UploadFile | None = File(None),
    image_right: UploadFile | None = File(None),
    image_left: UploadFile | None = File(None),
    image_plate: UploadFile | None = File(None),
):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    if await mongodb.db.vehicles.find_one({"plateNo": plateNo.upper()}):
        raise HTTPException(400, "Vehicle with this plate already exists")

    v_id = ObjectId()
    images = {}
    subdir = f"vehicles/{str(current['_id'])}/{str(v_id)}"
    if image_front: images["front"] = await save_image(image_front, subdir=subdir)
    if image_back:  images["back"]  = await save_image(image_back,  subdir=subdir)
    if image_right: images["right"] = await save_image(image_right, subdir=subdir)
    if image_left:  images["left"]  = await save_image(image_left,  subdir=subdir)
    if image_plate: images["plate"] = await save_image(image_plate, subdir=subdir)

    doc = vehicle_doc(
        ownerId=current["_id"],
        vehicleType=vehicleType,
        vehicleModel=vehicleModel,
        registrationDate=registrationDate,
        plateNo=plateNo,
        images=images,
    )
    doc["_id"] = v_id
    await mongodb.db.vehicles.insert_one(doc)

    return {
        "id": str(doc["_id"]),
        "ownerId": str(doc["ownerId"]),
        "vehicleType": doc["vehicleType"],
        "vehicleModel": doc["vehicleModel"],
        "registrationDate": doc["registrationDate"],
        "plateNo": doc["plateNo"],
        "images": doc["images"],
    }

@router.get("/mine", response_model=list[VehicleOut])
async def list_my_vehicles(current=Depends(get_current_owner)):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    cursor = mongodb.db.vehicles.find({"ownerId": current["_id"]})
    out = []
    async for v in cursor:
        out.append({
            "id": str(v["_id"]),
            "ownerId": str(v["ownerId"]),
            "vehicleType": v["vehicleType"],
            "vehicleModel": v["vehicleModel"],
            "registrationDate": v["registrationDate"],
            "plateNo": v["plateNo"],
            "images": v.get("images", {}),
        })
    return out

@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: str, current=Depends(get_current_owner)):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    v = await mongodb.db.vehicles.find_one({"_id": ObjectId(vehicle_id), "ownerId": current["_id"]})
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return {
        "id": str(v["_id"]),
        "ownerId": str(v["ownerId"]),
        "vehicleType": v["vehicleType"],
        "vehicleModel": v["vehicleModel"],
        "registrationDate": v["registrationDate"],
        "plateNo": v["plateNo"],
        "images": v.get("images", {}),
    }

@router.put("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: str,
    current=Depends(get_current_owner),
    vehicleType: Optional[str] = Form(None),
    vehicleModel: Optional[str] = Form(None),
    registrationDate: Optional[str] = Form(None),
    plateNo: Optional[str] = Form(None),
    image_front: UploadFile | None = File(None),
    image_back: UploadFile | None = File(None),
    image_right: UploadFile | None = File(None),
    image_left: UploadFile | None = File(None),
    image_plate: UploadFile | None = File(None),
):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    v = await mongodb.db.vehicles.find_one({"_id": ObjectId(vehicle_id), "ownerId": current["_id"]})
    if not v:
        raise HTTPException(404, "Vehicle not found")

    update = {}
    if vehicleType is not None: update["vehicleType"] = vehicleType
    if vehicleModel is not None: update["vehicleModel"] = vehicleModel
    if registrationDate is not None: update["registrationDate"] = registrationDate
    if plateNo is not None:
        exist = await mongodb.db.vehicles.find_one({"plateNo": plateNo.upper(), "_id": {"$ne": v["_id"]}})
        if exist:
            raise HTTPException(400, "Another vehicle already has this plate number")
        update["plateNo"] = plateNo.upper()

    images = v.get("images", {})
    subdir = f"vehicles/{str(current['_id'])}/{vehicle_id}"
    if image_front: images["front"] = await save_image(image_front, subdir=subdir)
    if image_back:  images["back"]  = await save_image(image_back,  subdir=subdir)
    if image_right: images["right"] = await save_image(image_right, subdir=subdir)
    if image_left:  images["left"]  = await save_image(image_left,  subdir=subdir)
    if image_plate: images["plate"] = await save_image(image_plate, subdir=subdir)
    if images != v.get("images", {}):
        update["images"] = images

    if not update:
        return {
            "id": str(v["_id"]),
            "ownerId": str(v["ownerId"]),
            "vehicleType": v["vehicleType"],
            "vehicleModel": v["vehicleModel"],
            "registrationDate": v["registrationDate"],
            "plateNo": v["plateNo"],
            "images": v.get("images", {}),
        }

    await mongodb.db.vehicles.update_one({"_id": v["_id"]}, {"$set": update})
    nv = await mongodb.db.vehicles.find_one({"_id": v["_id"]})
    return {
        "id": str(nv["_id"]),
        "ownerId": str(nv["ownerId"]),
        "vehicleType": nv["vehicleType"],
        "vehicleModel": nv["vehicleModel"],
        "registrationDate": nv["registrationDate"],
        "plateNo": str(nv["plateNo"]),
        "images": nv.get("images", {}),
    }

@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(vehicle_id: str, current=Depends(get_current_owner)):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    result = await mongodb.db.vehicles.delete_one({"_id": ObjectId(vehicle_id), "ownerId": current["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(404, "Vehicle not found")
    return
