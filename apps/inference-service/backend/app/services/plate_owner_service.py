import cv2
import torch
import numpy as np
from datetime import datetime
import logging
import base64
import re
from app.core.config import settings
import app.db.mongodb as mongodb
from app.models.violation_model import violation_doc
from app.utils.notifications import send_notification_to_owner
import traceback

logger = logging.getLogger(__name__)

class PlateOwnerService:
    def __init__(self):
        self.model = None
        self.ocr_reader = None
        self.confidence_threshold = settings.DETECTION_CONFIDENCE
        self.load_model()
        self.load_ocr_reader()
        
    def load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(settings.YOLO_MODEL)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO: {e}")
            return False

    def load_ocr_reader(self):
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available(), 
                                           model_storage_directory='./models',
                                           download_enabled=True)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load OCR: {e}")
            return False

    def preprocess_plate_image(self, plate_img):
        """
        Specialized for Sri Lankan plates with 'Carbon Fiber' texture
        """
        if plate_img is None or plate_img.size == 0: return None
        
        # 1. Upscale
        height, width = plate_img.shape[:2]
        scale = 3
        img = cv2.resize(plate_img, (int(width*scale), int(height*scale)), interpolation=cv2.INTER_CUBIC)
        
        # 2. Convert to Gray
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. Gaussian Blur (Reduces noise from the texture)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 4. Adaptive Thresholding (Better for uneven lighting)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 19, 9)
        
        # 5. MORPHOLOGICAL CLOSING (The Magic Step)
        # This fills the gaps in the "carbon fiber" texture to make letters solid
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # 6. Invert back to Black text on White background for OCR
        final_img = cv2.bitwise_not(closed)
        
        # Return different versions for OCR to try
        return {
            'morph': final_img,    # Best for textured plates
            'gray': gray,          # Fallback
            'thresh': thresh       # Fallback
        }

    def format_sri_lankan_plate(self, text_blob):
        """
        Parses OCR result string to find valid Sri Lankan formats.
        """
        clean_text = re.sub(r'[^A-Z0-9]', '', text_blob.upper())
        corrections = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'G': '6', 'B': '8'}
        
        # Look for pattern at the END of string to avoid Province codes like "NW"
        pattern = re.search(r'([A-Z]{2,3})([0-9]{4})$', clean_text)
        
        if pattern:
            letters = pattern.group(1)
            numbers = pattern.group(2)
            fixed_numbers = "".join([corrections.get(c, c) if c.isalpha() else c for c in numbers])
            return f"{letters} {fixed_numbers}"

        # Fallback: Strip province codes from start
        provinces = ["WP", "CP", "SP", "NP", "EP", "NW", "NC", "UP", "SG"]
        for prov in provinces:
            if clean_text.startswith(prov):
                clean_text = clean_text[2:]
                break
        
        match = re.search(r'([A-Z]{2,3})([0-9]{4})', clean_text)
        if match:
             return f"{match.group(1)} {match.group(2)}"
             
        return clean_text

    def perform_ocr(self, plate_region):
        if not self.ocr_reader: return []
        
        processed_imgs = self.preprocess_plate_image(plate_region)
        if not processed_imgs: return []
        
        strategies = ['morph', 'gray'] 
        best_text = ""
        best_conf = 0.0
        
        for strategy in strategies:
            img = processed_imgs[strategy]
            try:
                results = self.ocr_reader.readtext(
                    img,
                    decoder='greedy',
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                    batch_size=1, 
                    detail=1,
                    paragraph=False,
                    mag_ratio=3.0,
                    text_threshold=0.6,
                    link_threshold=0.4,
                    canvas_size=1280
                )
                
                full_text_blob = "".join([res[1] for res in results])
                
                if results:
                    avg_conf = sum([res[2] for res in results]) / len(results)
                    formatted = self.format_sri_lankan_plate(full_text_blob)
                    
                    if len(formatted) > 5 and avg_conf > best_conf:
                        best_text = formatted
                        best_conf = avg_conf
                        
            except Exception as e:
                pass

        if best_text:
            return [{'text': best_text, 'confidence': best_conf}]
        return []

    def detect_and_read_plate(self, image_bytes):
        try:
            if self.model is None: return None

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None: return None
            
            # YOLO Detect
            results = self.model(img, conf=0.25, verbose=False)
            if not results or len(results[0].boxes) == 0: return None
                
            best_box = results[0].boxes[0]
            x1, y1, x2, y2 = map(int, best_box.xyxy[0])
            conf = float(best_box.conf[0])
            
            # Crop
            h, w = img.shape[:2]
            pad_x, pad_y = int((x2-x1)*0.05), int((y2-y1)*0.05)
            crop_x1, crop_y1 = max(0, x1-pad_x), max(0, y1-pad_y)
            crop_x2, crop_y2 = min(w, x2+pad_x), min(h, y2+pad_y)
            plate_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
            
            # OCR
            ocr_results = self.perform_ocr(plate_crop)
            
            final_text = "NO_PLATE"
            ocr_conf = 0.0
            
            if ocr_results:
                final_text = ocr_results[0]['text']
                ocr_conf = ocr_results[0]['confidence']
                logger.info(f"✅ OCR Result: {final_text}")
            
            # Visualization
            annotated = img.copy()
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, final_text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            _, img_buf = cv2.imencode('.jpg', annotated)
            _, crop_buf = cv2.imencode('.jpg', plate_crop)

            return {
                'plate_number': final_text,
                'confidence': conf,
                'ocr_confidence': ocr_conf,
                'annotated_image': base64.b64encode(img_buf).decode('utf-8'),
                'cropped_plate_image': base64.b64encode(crop_buf).decode('utf-8')
            }
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return None

    async def find_vehicle_owner(self, plate_number):
        if plate_number == "NO_PLATE": return None
        
        search_key = plate_number.replace(" ", "").upper()
        
        try:
            if mongodb.db is None: return None
            
            vehicle = await mongodb.db.db.vehicles.find_one({
                "plateNo": {"$regex": f"^{search_key}$", "$options": "i"}
            })
            
            if not vehicle:
                relaxed = ".*".join(list(search_key))
                vehicle = await mongodb.db.db.vehicles.find_one({
                    "plateNo": {"$regex": f"^{relaxed}$", "$options": "i"}
                })

            if not vehicle: return None
            
            owner = await mongodb.db.db.users.find_one({"_id": vehicle["ownerId"]})
            if not owner: return None
            
            return {
                "vehicle": {"id": str(vehicle["_id"]), "plateNo": vehicle["plateNo"], "model": vehicle.get("vehicleModel"), "type": vehicle.get("vehicleType")},
                "owner": {"id": str(owner["_id"]), "name": owner.get("fullName"), "email": owner.get("email"), "phone": owner.get("phone"), "address": owner.get("address"), "nic": owner.get("nic")}
            }
        except Exception:
            return None

    async def process_complete_detection(self, image_bytes, location=None, camera_id=None):
        result = self.detect_and_read_plate(image_bytes)
        if not result or result['plate_number'] == "NO_PLATE":
            return {'success': False, 'error': 'No plate detected'}
            
        owner_info = await self.find_vehicle_owner(result['plate_number'])
        
        viol_id = None
        if owner_info:
            viol_id = await self.save_violation(
                result['plate_number'], result['confidence'], result['ocr_confidence'],
                image_bytes, location, camera_id, owner_info
            )
            
        notified = False
        if owner_info and viol_id:
            # FIX: Added 'location' parameter here to support the new notification system
            notified = await self.send_notification(
                owner_info, 
                result['plate_number'], 
                viol_id, 
                location if location else "Unknown Location"
            )
            
        result.update({
            'success': True,
            'violation_id': viol_id,
            'owner_info': owner_info,
            'notification_sent': notified,
            'timestamp': datetime.now().isoformat()
        })
        return result

    async def save_violation(self, plate_number, confidence, ocr_confidence,
                            image_bytes, location, camera_id, owner_info):
        try:
            if mongodb.db is None: return None
            violation = violation_doc(
                vehicleId=owner_info['vehicle']['id'],
                plateNumber=plate_number,
                detectionTime=datetime.utcnow(),
                location=location,
                cameraId=camera_id,
                confidence=confidence,
                ocr_confidence=ocr_confidence,
                notified=False,
                ownerId=owner_info['owner']['id']
            )
            res = await mongodb.db.db.violations.insert_one(violation)
            return str(res.inserted_id)
        except Exception:
            return None

    async def send_notification(self, owner_info, plate_number, violation_id, location="Unknown"):
        # Pass location and violation_id to the utils function
        return await send_notification_to_owner(
            owner=owner_info['owner'],
            plate_number=plate_number,
            detection_time=datetime.now(),
            violation_id=violation_id,
            location=location
        )

plate_owner_service = PlateOwnerService()