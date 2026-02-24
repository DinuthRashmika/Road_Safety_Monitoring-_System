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
from app.utils.images import save_detection_image  # ✅ NEW (only added)
import traceback

logger = logging.getLogger(__name__)

class PlateOwnerService:
    def __init__(self):
        self.plate_model = None
        self.violation_model = None
        self.ocr_reader = None
        self.confidence_threshold = settings.DETECTION_CONFIDENCE

        # Load everything
        self.load_models()
        self.load_ocr_reader()

    def load_models(self):
        try:
            from ultralytics import YOLO
            # 1. Load Plate Detection Model
            self.plate_model = YOLO(settings.YOLO_MODEL)
            logger.info(f"✅ Plate Model loaded: {settings.YOLO_MODEL}")

            # 2. Load Violation Detection Model
            self.violation_model = YOLO(settings.VIOLATION_MODEL)
            logger.info(f"✅ Violation Model loaded: {settings.VIOLATION_MODEL}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO models: {e}")
            return False

    def load_ocr_reader(self):
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(
                ['en'],
                gpu=torch.cuda.is_available(),
                model_storage_directory='./models',
                download_enabled=True
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load OCR: {e}")
            return False

    def preprocess_plate_image(self, plate_img):
        if plate_img is None or plate_img.size == 0:
            return None
        height, width = plate_img.shape[:2]
        scale = 3
        img = cv2.resize(
            plate_img,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_CUBIC
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 19, 9
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        final_img = cv2.bitwise_not(closed)
        return {'morph': final_img, 'gray': gray, 'thresh': thresh}

    def format_sri_lankan_plate(self, text_blob):
        clean_text = re.sub(r'[^A-Z0-9]', '', text_blob.upper())
        corrections = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'G': '6', 'B': '8'}

        pattern = re.search(r'([A-Z]{2,3})([0-9]{4})$', clean_text)
        if pattern:
            letters = pattern.group(1)
            numbers = pattern.group(2)
            fixed_numbers = "".join([corrections.get(c, c) if c.isalpha() else c for c in numbers])
            return f"{letters} {fixed_numbers}"

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
        if not self.ocr_reader:
            return []
        processed_imgs = self.preprocess_plate_image(plate_region)
        if not processed_imgs:
            return []
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
            except:
                pass

        if best_text:
            return [{'text': best_text, 'confidence': best_conf}]
        return []

    def detect_violation_type(self, img):
        if self.violation_model is None:
            return "Unknown", 0.0

        results = self.violation_model(img, conf=0.4, verbose=False)
        if not results or len(results[0].boxes) == 0:
            return "No Violation Detected", 0.0

        best_box = results[0].boxes[0]
        class_id = int(best_box.cls[0])
        conf = float(best_box.conf[0])
        violation_name = self.violation_model.names[class_id]
        return violation_name, conf

    def detect_and_read_plate_and_violation(self, image_bytes):
        try:
            if self.plate_model is None:
                return None

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None

            # 1. Detect Plate (main/violation vehicle plate)
            plate_results = self.plate_model(img, conf=0.25, verbose=False)
            final_text = "NO_PLATE"
            plate_conf = 0.0
            ocr_conf = 0.0
            plate_crop = None

            x1 = y1 = x2 = y2 = 0

            if plate_results and len(plate_results[0].boxes) > 0:
                best_box = plate_results[0].boxes[0]
                x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                plate_conf = float(best_box.conf[0])

                h, w = img.shape[:2]
                pad_x, pad_y = int((x2 - x1) * 0.05), int((y2 - y1) * 0.05)
                crop_x1, crop_y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
                crop_x2, crop_y2 = min(w, x2 + pad_x), min(h, y2 + pad_y)

                plate_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
                ocr_results = self.perform_ocr(plate_crop)
                if ocr_results:
                    final_text = ocr_results[0]['text']
                    ocr_conf = ocr_results[0]['confidence']

            # 2. Detect Violation Type
            violation_type, violation_conf = self.detect_violation_type(img)

            # 3. Calculate Fine
            fine = settings.VIOLATION_FINES.get(
                violation_type,
                settings.VIOLATION_FINES.get("default", 0.0)
            )
            if violation_type == "No Violation Detected":
                fine = 0.0

            # 4. Visualization
            annotated = img.copy()
            if plate_conf > 0:
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    annotated,
                    final_text,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

            label = f"Violation: {violation_type} (Fine: {fine})"
            cv2.putText(
                annotated,
                label,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            _, img_buf = cv2.imencode('.jpg', annotated)
            crop_b64 = None

            if plate_crop is not None:
                _, crop_buf = cv2.imencode('.jpg', plate_crop)
                crop_b64 = base64.b64encode(crop_buf).decode('utf-8')

            return {
                'plate_number': final_text,
                'confidence': plate_conf,
                'ocr_confidence': ocr_conf,
                'violation_type': violation_type,
                'violation_confidence': violation_conf,
                'fine_amount': fine,
                'annotated_image': base64.b64encode(img_buf).decode('utf-8'),
                'cropped_plate_image': crop_b64
            }

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return None

    # ----------------------- NEW METHOD (NOVELTY SUPPORT) -----------------------
    def extract_all_plates_from_image(self, image_bytes):
        """
        Detect ALL plate boxes in the image, OCR each one, return unique plates.
        Used to find nearby vehicles.
        """
        try:
            if self.plate_model is None:
                return []

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return []

            results = self.plate_model(img, conf=0.25, verbose=False)
            if not results or len(results[0].boxes) == 0:
                return []

            plates = []
            h, w = img.shape[:2]

            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                pad_x, pad_y = int((x2 - x1) * 0.05), int((y2 - y1) * 0.05)
                crop_x1, crop_y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
                crop_x2, crop_y2 = min(w, x2 + pad_x), min(h, y2 + pad_y)

                plate_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
                ocr_results = self.perform_ocr(plate_crop)

                if ocr_results:
                    txt = ocr_results[0]["text"]
                    if txt and len(txt) > 5:
                        plates.append(txt.strip().upper())

            return list(set(plates))  # unique
        except Exception as e:
            logger.error(f"extract_all_plates_from_image failed: {e}")
            return []
    # ---------------------------------------------------------------------------

    async def find_vehicle_owner(self, plate_number):
        if not plate_number or plate_number == "NO_PLATE":
            return None

        variations = [
            plate_number,
            plate_number.replace(" ", ""),
            plate_number.replace("-", ""),
            plate_number.replace(" ", "").replace("-", "")
        ]
        variations = list(set(variations))

        vehicle = None
        database = mongodb.db.db

        try:
            for key in variations:
                logger.info(f"🔍 Searching DB for vehicle plate: '{key}'")
                query = {
                    "$or": [
                        {"plateNo": {"$regex": f"^{key}$", "$options": "i"}},
                        {"plate_number": {"$regex": f"^{key}$", "$options": "i"}}
                    ]
                }
                vehicle = await database.vehicles.find_one(query)
                if vehicle:
                    logger.info(f"✅ Vehicle Found: {vehicle.get('plateNo')}")
                    break

            if not vehicle:
                logger.warning(f"❌ Vehicle not found in DB for input: {plate_number}")
                return None

            owner_id = vehicle.get("ownerId")
            if not owner_id:
                logger.error("Vehicle found but has no ownerId")
                return None

            owner = await database.users.find_one({"_id": owner_id})
            if not owner:
                owner = await database.owners.find_one({"_id": owner_id})

            if not owner:
                logger.error(f"Owner ID {owner_id} linked to vehicle but not found in Users/Owners collection")
                return None

            return {
                "vehicle": {
                    "id": str(vehicle["_id"]),
                    "plateNo": vehicle.get("plateNo"),
                    "model": vehicle.get("vehicleModel") or vehicle.get("model", "Unknown"),
                    "type": vehicle.get("vehicleType") or vehicle.get("type", "Car")
                },
                "owner": {
                    "id": str(owner["_id"]),
                    "name": owner.get("fullName") or owner.get("name"),
                    "email": owner.get("email"),
                    "phone": owner.get("phone"),
                    "address": owner.get("address"),
                    "nic": owner.get("nic")
                }
            }
        except Exception as e:
            logger.error(f"Error finding owner: {e}")
            return None

    async def process_complete_detection(self, image_bytes, location=None, camera_id=None):
        result = self.detect_and_read_plate_and_violation(image_bytes)

        if not result or result['plate_number'] == "NO_PLATE":
            return {'success': False, 'error': 'No plate detected'}

        owner_info = await self.find_vehicle_owner(result['plate_number'])

        viol_id = None
        notified = False

        if owner_info:
            logger.info(f"Processing violation for known owner: {owner_info['owner']['name']}")

            # ✅ NEW: Save violation image and store path
            image_path = save_detection_image(image_bytes, result['plate_number'])

            viol_id = await self.save_violation(
                result['plate_number'], result['confidence'], result['ocr_confidence'],
                result['violation_type'], result['fine_amount'], result['violation_confidence'],
                image_bytes, location, camera_id, owner_info,
                image_path=image_path  # ✅ NEW
            )

            if viol_id:
                logger.info(f"Violation saved with ID: {viol_id}. Sending notification...")
                notified = await self.send_notification(
                    owner_info,
                    result['plate_number'],
                    viol_id,
                    result['violation_type'],
                    result['fine_amount'],
                    location if location else "Unknown Location",
                    image_path=image_path  # ✅ NEW
                )

                # ------------------ NEW NOVELTY FEATURE BLOCK ------------------
                try:
                    from app.utils.protective_alerts import send_protective_alert_to_owner

                    all_plates = self.extract_all_plates_from_image(image_bytes)

                    viol_plate_norm = (result.get("plate_number") or "").replace(" ", "").replace("-", "").upper()

                    nearby_plates = []
                    for p in all_plates:
                        p_norm = p.replace(" ", "").replace("-", "").upper()
                        if p_norm and p_norm != viol_plate_norm:
                            nearby_plates.append(p)

                    nearby_plates = list(set(nearby_plates))

                    for near_plate in nearby_plates:
                        near_owner_info = await self.find_vehicle_owner(near_plate)
                        if not near_owner_info:
                            continue

                        if near_owner_info["owner"]["id"] == owner_info["owner"]["id"]:
                            continue

                        await send_protective_alert_to_owner(
                            owner=near_owner_info["owner"],
                            near_plate=near_plate,
                            location=location if location else "Unknown Location",
                            violation_id=viol_id,
                            violation_type=result.get("violation_type", "Unknown"),
                            violation_image=None
                        )

                except Exception as e:
                    logger.error(f"Nearby protective alert block failed: {e}")
                # -------------------------------------------------------------

        else:
            logger.warning("Skipping database save because Owner/Vehicle was not found.")

        result.update({
            'success': True,
            'violation_id': viol_id,
            'owner_info': owner_info,
            'notification_sent': notified,
            'timestamp': datetime.now().isoformat()
        })
        return result

    async def save_violation(self, plate_number, confidence, ocr_confidence,
                             violation_type, fine_amount, violation_confidence,
                             image_bytes, location, camera_id, owner_info,
                             image_path=None):  # ✅ NEW
        try:
            if mongodb.db is None:
                return None

            violation = violation_doc(
                vehicleId=owner_info['vehicle']['id'],
                plateNumber=plate_number,
                detectionTime=datetime.utcnow(),
                location=location,
                cameraId=camera_id,
                violationType=violation_type,
                fineAmount=fine_amount,
                violationConfidence=violation_confidence,
                confidence=confidence,
                ocr_confidence=ocr_confidence,
                notified=False,
                ownerId=owner_info['owner']['id'],
                imagePath=image_path  # ✅ NEW
            )
            res = await mongodb.db.db.violations.insert_one(violation)
            return str(res.inserted_id)

        except Exception as e:
            logger.error(f"Save error: {e}")
            return None

    async def send_notification(self, owner_info, plate_number, violation_id,
                                violation_type, fine_amount, location="Unknown",
                                image_path=None):  # ✅ NEW
        return await send_notification_to_owner(
            owner=owner_info['owner'],
            plate_number=plate_number,
            violation_type=violation_type,
            fine_amount=fine_amount,
            detection_time=datetime.now(),
            violation_id=violation_id,
            location=location,
            image_path=image_path  # ✅ NEW
        )

plate_owner_service = PlateOwnerService()