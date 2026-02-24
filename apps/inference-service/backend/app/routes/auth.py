from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
import app.db.mongodb as mongodb
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import OwnerOut
from app.schemas.auth import TokenOut
from app.models.user_model import user_doc
from app.utils.images import save_image, make_public_url
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register-owner", response_model=OwnerOut, status_code=201)
async def register_owner(
    request: Request,
    fullName: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    nic: str = Form(...),
    password: str = Form(...),
    image: UploadFile | None = File(None),
):
    """Register a new vehicle owner"""
    try:
        if mongodb.db is None or mongodb.db.db is None:
            logger.error("Database not initialized")
            raise HTTPException(500, "Database not initialized")
        
        database = mongodb.db.db
        
        # Check existing user
        existing_email = await database.users.find_one({"email": email.lower()})
        if existing_email:
            raise HTTPException(400, "Email already registered")
        
        existing_nic = await database.users.find_one({"nic": nic.upper()})
        if existing_nic:
            raise HTTPException(400, "NIC already registered")
        
        # Save image
        imageUrl = None
        if image and image.filename:
            try:
                rel_path = await save_image(image, subdir="owners")
                imageUrl = rel_path
            except Exception as e:
                logger.error(f"Failed to save image: {e}")
        
        # Create user
        doc = user_doc(
            fullName=fullName,
            email=email,
            phone=phone,
            address=address,
            nic=nic,
            passwordHash=hash_password(password),
            imageUrl=imageUrl,
        )
        
        result = await database.users.insert_one(doc)
        
        public_image = make_public_url(request, imageUrl)
        
        return {
            "id": str(result.inserted_id),
            "fullName": doc["fullName"],
            "email": doc["email"],
            "phone": doc["phone"],
            "address": doc["address"],
            "nic": doc["nic"],
            "role": doc["role"],
            "imageUrl": public_image,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(500, f"Registration failed: {str(e)}")

@router.post("/login", response_model=TokenOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint"""
    try:
        if mongodb.db is None or mongodb.db.db is None:
            logger.error("Database not connected during login attempt")
            raise HTTPException(500, "Database not initialized")
        
        database = mongodb.db.db
        username = form_data.username.strip().lower()
        password = form_data.password
        
        logger.info(f"Login attempt for: {username}")
        
        # Find user
        user = await database.users.find_one({
            "$or": [
                {"email": username},
                {"nic": username.upper()}
            ]
        })
        
        if not user:
            logger.warning(f"User not found: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(password, user["passwordHash"]):
            logger.warning(f"Invalid password for: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create Token
        token_data = {
            "sub": str(user["_id"]),
            "role": user.get("role", "owner"),
            "email": user["email"]
        }
        token = create_access_token(token_data)
        
        logger.info(f"Login successful: {username}")
        return {"access_token": token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        # THIS LOG WILL SHOW IN YOUR TERMINAL IF IT FAILS AGAIN
        logger.error(f"CRITICAL LOGIN ERROR: {str(e)}") 
        raise HTTPException(500, f"Login failed: {str(e)}")