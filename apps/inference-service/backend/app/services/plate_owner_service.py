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
from app.utils.images import save_detection_image
import traceback

logger = logging.getLogger(__name__)

PLATE_CONF_FULL = 0.10   # full image pass  (was 0.25 — bike plate was being dropped)
PLATE_CONF_TILE = 0.08   # tile pass fallback
MIN_PLATE_LEN   = 5


class PlateOwnerService:
    def __init__(self):
        self.plate_model     = None
        self.violation_model = None
        self.ocr_reader      = None
        self.confidence_threshold = settings.DETECTION_CONFIDENCE
        self.load_models()
        self.load_ocr_reader()

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    def load_models(self):
        try:
            from ultralytics import YOLO
            self.plate_model     = YOLO(settings.YOLO_MODELS)
            logger.info(f"✅ Plate Model loaded: {settings.YOLO_MODELS}")
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

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
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
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur  = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 19, 9
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        final_img = cv2.bitwise_not(closed)

        clahe      = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_gray = clahe.apply(gray)
        mid        = img.shape[0] // 2
        top_half   = gray[:mid, :]
        bot_half   = gray[mid:, :]

        return {
            'morph'   : final_img,
            'gray'    : gray,
            'thresh'  : thresh,
            'clahe'   : clahe_gray,
            'top_half': top_half,
            'bot_half': bot_half,
        }

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
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

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    def perform_ocr(self, plate_region):
        if not self.ocr_reader:
            return []
        processed_imgs = self.preprocess_plate_image(plate_region)
        if not processed_imgs:
            return []

        best_text = ""
        best_conf = 0.0

        for strategy in ['morph', 'gray', 'clahe']:
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
                    text_threshold=0.5,
                    link_threshold=0.3,
                    canvas_size=1280
                )
                full_text_blob = "".join([res[1] for res in results])
                if results:
                    avg_conf  = sum([res[2] for res in results]) / len(results)
                    formatted = self.format_sri_lankan_plate(full_text_blob)
                    if len(formatted) > 5 and avg_conf > best_conf:
                        best_text = formatted
                        best_conf = avg_conf
            except:
                pass

        # Two-row strategy — fixes stacked plates like CBH/6301 → CBA misread
        try:
            top_res = self.ocr_reader.readtext(
                processed_imgs['top_half'],
                decoder='greedy',
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                detail=1, paragraph=False,
                text_threshold=0.4, link_threshold=0.3,
            )
            bot_res = self.ocr_reader.readtext(
                processed_imgs['bot_half'],
                decoder='greedy',
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                detail=1, paragraph=False,
                text_threshold=0.4, link_threshold=0.3,
            )
            top_text = "".join(r[1] for r in top_res)
            bot_text = "".join(r[1] for r in bot_res)
            if top_text and bot_text:
                combined  = top_text + bot_text
                all_res   = top_res + bot_res
                avg_conf  = sum(r[2] for r in all_res) / len(all_res)
                formatted = self.format_sri_lankan_plate(combined)
                if len(formatted) > 5 and avg_conf > best_conf:
                    best_text = formatted
                    best_conf = avg_conf
        except:
            pass

        if best_text:
            return [{'text': best_text, 'confidence': best_conf}]
        return []

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    def detect_violation_type(self, img):
        if self.violation_model is None:
            return "Unknown", 0.0, None   # returns bbox too now

        results = self.violation_model(img, conf=0.4, verbose=False)
        if not results or len(results[0].boxes) == 0:
            return "No Violation Detected", 0.0, None

        best_box   = results[0].boxes[0]
        class_id   = int(best_box.cls[0])
        conf       = float(best_box.conf[0])
        viol_name  = self.violation_model.names[class_id]

        # Return the violation bounding box so we can match it to the nearest plate
        vx1, vy1, vx2, vy2 = map(int, best_box.xyxy[0])
        viol_bbox = (vx1, vy1, vx2, vy2)

        return viol_name, conf, viol_bbox

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: centre point of a bounding box
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _bbox_centre(bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: Euclidean distance between two (cx, cy) points
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _distance(p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    # ─────────────────────────────────────────────────────────────────────────
    # Detect ALL plates: full image + tile fallback, deduped, sorted
    # ─────────────────────────────────────────────────────────────────────────
    def _detect_all_plates(self, img):
        """
        Internal helper. Runs YOLO on the full image + 4 tiles.
        Returns list of plate dicts sorted by detection confidence desc.
        Each dict: { plate_number, confidence, ocr_confidence, bbox, crop_b64 }
        """
        h, w = img.shape[:2]
        detected = []

        # ── Pass 1: full image ────────────────────────────────────────────────
        results = self.plate_model(img, conf=PLATE_CONF_FULL, verbose=False)
        if results and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                det_conf = float(box.conf[0])
                px  = int((x2 - x1) * 0.05);  py = int((y2 - y1) * 0.05)
                cx1 = max(0, x1 - px);         cy1 = max(0, y1 - py)
                cx2 = min(w, x2 + px);         cy2 = min(h, y2 + py)
                crop    = img[cy1:cy2, cx1:cx2]
                ocr_res = self.perform_ocr(crop)
                plate_text = ocr_res[0]['text'] if ocr_res else "NO_PLATE"
                ocr_conf   = ocr_res[0]['confidence'] if ocr_res else 0.0
                crop_b64   = None
                try:
                    _, buf = cv2.imencode('.jpg', crop)
                    crop_b64 = base64.b64encode(buf).decode('utf-8')
                except:
                    pass
                detected.append({
                    'plate_number'  : plate_text,
                    'confidence'    : det_conf,
                    'ocr_confidence': ocr_conf,
                    'bbox'          : (x1, y1, x2, y2),
                    'crop_b64'      : crop_b64,
                })

        # ── Pass 2: tile scan ─────────────────────────────────────────────────
        tiles = [
            (img[:, :w//2], 0,    0),
            (img[:, w//2:], w//2, 0),
            (img[:h//2, :], 0,    0),
            (img[h//2:, :], 0,    h//2),
        ]
        for tile_img, x_off, y_off in tiles:
            tile_res = self.plate_model(tile_img, conf=PLATE_CONF_TILE, verbose=False)
            if not tile_res or len(tile_res[0].boxes) == 0:
                continue
            th, tw = tile_img.shape[:2]
            for box in tile_res[0].boxes:
                tx1, ty1, tx2, ty2 = map(int, box.xyxy[0])
                det_conf = float(box.conf[0])
                px  = int((tx2 - tx1) * 0.05); py = int((ty2 - ty1) * 0.05)
                cx1 = max(0, tx1 - px);        cy1 = max(0, ty1 - py)
                cx2 = min(tw, tx2 + px);       cy2 = min(th, ty2 + py)
                crop    = tile_img[cy1:cy2, cx1:cx2]
                ocr_res = self.perform_ocr(crop)
                plate_text = ocr_res[0]['text'] if ocr_res else "NO_PLATE"
                ocr_conf   = ocr_res[0]['confidence'] if ocr_res else 0.0
                if plate_text == "NO_PLATE":
                    continue
                abs_bbox = (tx1 + x_off, ty1 + y_off, tx2 + x_off, ty2 + y_off)
                crop_b64 = None
                try:
                    _, buf = cv2.imencode('.jpg', crop)
                    crop_b64 = base64.b64encode(buf).decode('utf-8')
                except:
                    pass
                detected.append({
                    'plate_number'  : plate_text,
                    'confidence'    : det_conf,
                    'ocr_confidence': ocr_conf,
                    'bbox'          : abs_bbox,
                    'crop_b64'      : crop_b64,
                })

        # ── Deduplicate by normalised text ────────────────────────────────────
        seen   = set()
        unique = []
        for p in detected:
            norm = p['plate_number'].replace(" ", "").replace("-", "").upper()
            if norm in ("NOPLATE", "") or len(norm) < MIN_PLATE_LEN:
                continue
            if norm not in seen:
                seen.add(norm)
                unique.append(p)

        unique.sort(key=lambda d: d['confidence'], reverse=True)
        return unique

    # ─────────────────────────────────────────────────────────────────────────
    # KEY METHOD — identifies which plate is the VIOLATION vehicle
    # and which are NEARBY vehicles using spatial proximity to the
    # violation bounding box returned by the violation model.
    #
    # Why this matters:
    #   When YOLO detects a "no_helmet" violation, it draws a box around
    #   the person/bike committing the violation.  The plate physically
    #   closest to that box belongs to the violation vehicle.
    #   All other plates are nearby (innocent) vehicles.
    #
    # Fallback (no violation bbox or no plates near it):
    #   Use highest-confidence plate as violation vehicle.
    # ─────────────────────────────────────────────────────────────────────────
    def _split_violation_and_nearby(self, all_plates, viol_bbox):
        """
        Returns (violation_plate_dict, [nearby_plate_dict, ...])
        """
        if not all_plates:
            return None, []

        if len(all_plates) == 1:
            return all_plates[0], []

        # If no violation bbox available, fall back to highest-confidence plate
        if viol_bbox is None:
            return all_plates[0], all_plates[1:]

        viol_centre = self._bbox_centre(viol_bbox)

        # Find the plate whose centre is closest to the violation bbox centre
        closest     = None
        closest_dist = float('inf')
        for p in all_plates:
            plate_centre = self._bbox_centre(p['bbox'])
            dist = self._distance(viol_centre, plate_centre)
            if dist < closest_dist:
                closest_dist = dist
                closest      = p

        nearby = [p for p in all_plates if p is not closest]
        return closest, nearby

    # ─────────────────────────────────────────────────────────────────────────
    # Main image pipeline
    # ─────────────────────────────────────────────────────────────────────────
    def detect_and_read_plate_and_violation(self, image_bytes):
        try:
            if self.plate_model is None:
                return None

            nparr = np.frombuffer(image_bytes, np.uint8)
            img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None

            # 1. Detect ALL plates
            all_plates = self._detect_all_plates(img)

            # 2. Detect violation type + its bounding box
            violation_type, violation_conf, viol_bbox = self.detect_violation_type(img)

            # 3. Identify violation plate vs nearby plates by spatial proximity
            violation_plate, nearby_plates = self._split_violation_and_nearby(
                all_plates, viol_bbox
            )

            # 4. Calculate fine
            fine = settings.VIOLATION_FINES.get(
                violation_type,
                settings.VIOLATION_FINES.get("default", 0.0)
            )
            if violation_type == "No Violation Detected":
                fine = 0.0

            # 5. Console log — all plates with their roles
            print("\n" + "=" * 65)
            print("  📷  ALL DETECTED PLATES IN IMAGE")
            print(f"  🚨  Violation : {violation_type}")
            print("=" * 65)
            if not all_plates:
                print("  ⚠️   No plates detected.")
            for p in all_plates:
                role = "🔴 VIOLATION VEHICLE" if p is violation_plate else "🟠 NEARBY VEHICLE"
                print(f"  {role}  |  Plate: {p['plate_number']:<12}"
                      f"  det:{p['confidence']:.2f}  ocr:{p['ocr_confidence']:.2f}")
            print("=" * 65 + "\n")

            # 6. Primary values (violation plate)
            final_text = violation_plate['plate_number']    if violation_plate else "NO_PLATE"
            plate_conf = violation_plate['confidence']       if violation_plate else 0.0
            ocr_conf   = violation_plate['ocr_confidence']   if violation_plate else 0.0
            crop_b64   = violation_plate['crop_b64']         if violation_plate else None

            # 7. Annotate image
            annotated = img.copy()
            for p in all_plates:
                bx1, by1, bx2, by2 = p['bbox']
                if p is violation_plate:
                    color = (0, 0, 255)    # Red   = violation vehicle
                    tag   = "VIOLATION"
                else:
                    color = (0, 165, 255)  # Orange = nearby vehicle
                    tag   = "NEARBY"
                cv2.rectangle(annotated, (bx1, by1), (bx2, by2), color, 2)
                cv2.putText(
                    annotated,
                    f"{p['plate_number']} [{tag}]",
                    (bx1, by1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2
                )

            # Draw violation bbox if available
            if viol_bbox:
                vx1, vy1, vx2, vy2 = viol_bbox
                cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (255, 0, 0), 2)
                cv2.putText(annotated, violation_type, (vx1, vy1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            cv2.putText(annotated, f"Violation: {violation_type} (Fine: {fine})",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            _, img_buf = cv2.imencode('.jpg', annotated)

            return {
                'plate_number'        : final_text,
                'confidence'          : plate_conf,
                'ocr_confidence'      : ocr_conf,
                'violation_type'      : violation_type,
                'violation_confidence': violation_conf,
                'fine_amount'         : fine,
                'annotated_image'     : base64.b64encode(img_buf).decode('utf-8'),
                'cropped_plate_image' : crop_b64,
                # Internal — used by process_complete_detection
                '_violation_plate'    : violation_plate,
                '_nearby_plates'      : nearby_plates,
            }

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return None

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    def extract_all_plates_from_image(self, image_bytes, already_found=None):
        """
        Returns list of unique plate number strings.
        Reuses already_found if provided (avoids second YOLO run).
        """
        try:
            if already_found is not None:
                return [p['plate_number'] for p in already_found
                        if p['plate_number'] != "NO_PLATE"
                        and len(p['plate_number']) > MIN_PLATE_LEN]

            if self.plate_model is None:
                return []

            nparr = np.frombuffer(image_bytes, np.uint8)
            img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return []

            plates = self._detect_all_plates(img)
            return [p['plate_number'] for p in plates]

        except Exception as e:
            logger.error(f"extract_all_plates_from_image failed: {e}")
            return []

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    async def find_vehicle_owner(self, plate_number):
        if not plate_number or plate_number == "NO_PLATE":
            return None

        variations = list(set([
            plate_number,
            plate_number.replace(" ", ""),
            plate_number.replace("-", ""),
            plate_number.replace(" ", "").replace("-", "")
        ]))

        vehicle  = None
        database = mongodb.db.db

        try:
            for key in variations:
                logger.info(f"🔍 Searching DB for vehicle plate: '{key}'")
                query = {
                    "$or": [
                        {"plateNo":      {"$regex": f"^{key}$", "$options": "i"}},
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
                logger.error(f"Owner ID {owner_id} not found in users/owners collection")
                return None

            return {
                "vehicle": {
                    "id":      str(vehicle["_id"]),
                    "plateNo": vehicle.get("plateNo"),
                    "model":   vehicle.get("vehicleModel") or vehicle.get("model", "Unknown"),
                    "type":    vehicle.get("vehicleType")  or vehicle.get("type",  "Car")
                },
                "owner": {
                    "id":      str(owner["_id"]),
                    "name":    owner.get("fullName") or owner.get("name"),
                    "email":   owner.get("email"),
                    "phone":   owner.get("phone"),
                    "address": owner.get("address"),
                    "nic":     owner.get("nic")
                }
            }
        except Exception as e:
            logger.error(f"Error finding owner: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────
    async def process_complete_detection(self, image_bytes, location=None, camera_id=None):
        result = self.detect_and_read_plate_and_violation(image_bytes)

        if not result or result['plate_number'] == "NO_PLATE":
            return {'success': False, 'error': 'No plate detected'}

        # Pull out the pre-split plates (no second YOLO run needed)
        violation_plate_dict = result.get('_violation_plate')   # dict with bbox, plate_number …
        nearby_plate_dicts   = result.get('_nearby_plates', []) # list of dicts

        violation_plate_number = violation_plate_dict['plate_number'] if violation_plate_dict else result['plate_number']
        nearby_plate_numbers   = [p['plate_number'] for p in nearby_plate_dicts
                                  if p['plate_number'] != "NO_PLATE"]

        # ── A: Look up violation vehicle owner and send VIOLATION REPORT ──────
        owner_info = await self.find_vehicle_owner(violation_plate_number)

        viol_id  = None
        notified = False

        if owner_info:
            logger.info(f"🚨 Violation vehicle : {violation_plate_number}")
            logger.info(f"   Owner            : {owner_info['owner']['name']}")
            logger.info(f"   Violation        : {result['violation_type']}")
            logger.info(f"   Fine             : LKR {result['fine_amount']}")

            image_path = save_detection_image(image_bytes, violation_plate_number)

            viol_id = await self.save_violation(
                violation_plate_number,
                result['confidence'],
                result['ocr_confidence'],
                result['violation_type'],
                result['fine_amount'],
                result['violation_confidence'],
                image_bytes, location, camera_id, owner_info,
                image_path=image_path
            )

            if viol_id:
                logger.info(f"   📩 Sending VIOLATION REPORT → {owner_info['owner']['name']} ({violation_plate_number})")
                notified = await self.send_notification(
                    owner_info,
                    violation_plate_number,
                    viol_id,
                    result['violation_type'],
                    result['fine_amount'],
                    location if location else "Unknown Location",
                    image_path=image_path
                )
        else:
            logger.warning(f"⚠️  No registered owner for violation plate: {violation_plate_number}")

        # ── B: Send PROTECTIVE ALERTS to nearby vehicle owners ────────────────
        if nearby_plate_numbers:
            logger.info(f"\n🔎 {len(nearby_plate_numbers)} nearby plate(s) found — sending protective alerts...")
            try:
                from app.utils.protective_alerts import send_protective_alert_to_owner

                # Console summary
                print("\n" + "=" * 65)
                print(f"  🔴  VIOLATION  → [{violation_plate_number}]  violation report sent")
                for np_ in nearby_plate_numbers:
                    print(f"  🟠  NEARBY     → [{np_}]  protective alert will be sent")
                print("=" * 65 + "\n")

                for near_plate in nearby_plate_numbers:
                    near_owner_info = await self.find_vehicle_owner(near_plate)
                    if not near_owner_info:
                        logger.warning(f"   ⚠️  No owner found for nearby plate: {near_plate}")
                        continue

                    # Never alert the same owner twice
                    if owner_info and near_owner_info["owner"]["id"] == owner_info["owner"]["id"]:
                        logger.info(f"   ℹ️  Same owner as violation vehicle — skipping")
                        continue

                    logger.info(
                        f"   🛡️  Sending PROTECTIVE ALERT → "
                        f"{near_owner_info['owner']['name']} ({near_plate})"
                    )
                    await send_protective_alert_to_owner(
                        owner          = near_owner_info["owner"],
                        near_plate     = near_plate,
                        location       = location if location else "Unknown Location",
                        violation_id   = viol_id,
                        violation_type = result.get("violation_type", "Unknown"),
                        violation_image= None
                    )

            except Exception as e:
                logger.error(f"Nearby protective alert block failed: {e}")
        else:
            logger.info("ℹ️  No nearby plates — no protective alerts to send.")

        result.update({
            'success'          : True,
            'violation_id'     : viol_id,
            'owner_info'       : owner_info,
            'notification_sent': notified,
            'timestamp'        : datetime.now().isoformat()
        })
        return result

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    async def save_violation(self, plate_number, confidence, ocr_confidence,
                             violation_type, fine_amount, violation_confidence,
                             image_bytes, location, camera_id, owner_info,
                             image_path=None):
        try:
            if mongodb.db is None:
                return None
            violation = violation_doc(
                vehicleId           = owner_info['vehicle']['id'],
                plateNumber         = plate_number,
                detectionTime       = datetime.utcnow(),
                location            = location,
                cameraId            = camera_id,
                violationType       = violation_type,
                fineAmount          = fine_amount,
                violationConfidence = violation_confidence,
                confidence          = confidence,
                ocr_confidence      = ocr_confidence,
                notified            = False,
                ownerId             = owner_info['owner']['id'],
                imagePath           = image_path
            )
            res = await mongodb.db.db.violations.insert_one(violation)
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Save error: {e}")
            return None

    # ── UNCHANGED ─────────────────────────────────────────────────────────────
    async def send_notification(self, owner_info, plate_number, violation_id,
                                violation_type, fine_amount, location="Unknown",
                                image_path=None):
        return await send_notification_to_owner(
            owner          = owner_info['owner'],
            plate_number   = plate_number,
            violation_type = violation_type,
            fine_amount    = fine_amount,
            detection_time = datetime.now(),
            violation_id   = violation_id,
            location       = location,
            image_path     = image_path
        )


plate_owner_service = PlateOwnerService()