from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
import app.db.mongodb as mongodb  # <-- use module
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import OwnerOut
from app.schemas.auth import TokenOut
from app.models.user_model import user_doc
from app.utils.images import save_image

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register-owner", response_model=OwnerOut, status_code=201)
async def register_owner(
    fullName: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    nic: str = Form(...),
    password: str = Form(...),
    image: UploadFile | None = File(None),
):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    if await mongodb.db.users.find_one({"email": email.lower()}):
        raise HTTPException(400, "Email already registered")
    if await mongodb.db.users.find_one({"nic": nic.upper()}):
        raise HTTPException(400, "NIC already registered")

    imageUrl = None
    if image:
        imageUrl = await save_image(image, subdir="owners")

    doc = user_doc(
        fullName=fullName,
        email=email,
        phone=phone,
        address=address,
        nic=nic,
        passwordHash=hash_password(password),
        imageUrl=imageUrl,
    )
    res = await mongodb.db.users.insert_one(doc)
    return {
        "id": str(res.inserted_id),
        "fullName": doc["fullName"],
        "email": doc["email"],
        "phone": doc["phone"],
        "address": doc["address"],
        "nic": doc["nic"],
        "role": doc["role"],
        "imageUrl": doc["imageUrl"],
    }

@router.post("/login", response_model=TokenOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if mongodb.db is None:
        raise HTTPException(500, "DB not initialized")

    username = form_data.username.strip()
    user = await mongodb.db.users.find_one({
        "$or": [{"email": username.lower()}, {"nic": username.upper()}]
    })
    if not user or not verify_password(form_data.password, user["passwordHash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return {"access_token": token}
