import asyncio
import cv2
from ultralytics import YOLO
from datetime import datetime
from app.db.mongo import get_db, get_client
from app.modules.incidents.schemas import Incident, Accident  
from app.modules.responders.schemas import Location           
from app.modules.incidents.priority import score_incident

# 1. Load your newly trained Accident Detection Model
try:
    accident_model = YOLO("app/accident_model.pt")
    print("Accident AI Model loaded successfully.")
except Exception as e:
    print(f"Failed to load AI model: {e}")

async def process_shared_database():
    while True:
        try:
            # 2. Database Connections
            client = get_client()
            my_db = get_db()
            
            friend_collection = client["road_safty"]["violations"]
            
            cursor = friend_collection.find({"processed": {"$ne": True}})
            new_rows = await cursor.to_list(length=100)
            
            if new_rows:
                grouped_events = {}
                for row in new_rows:
                    event_key = f"{row.get('location')}_{row.get('time')}"
                    if event_key not in grouped_events:
                        grouped_events[event_key] = []
                    grouped_events[event_key].append(row)

                for event_key, vehicles in grouped_events.items():
                    first_vehicle = vehicles[0]
                    image_path = first_vehicle.get("image_path")
                    
                    is_accident = False
                    
                    if image_path:
                        try:
                            img = cv2.imread(image_path)
                            if img is not None:
                                results = accident_model(img, conf=0.5) 
                                
                                for r in results:
                                    if len(r.boxes) > 0:
                                        is_accident = True
                                        break
                            else:
                                print(f"Could not read image file at {image_path}")
                        except Exception as e:
                            print(f"Error processing image {image_path}: {e}")

                    if is_accident:
                        print(f"🚨 AI DETECTED ACCIDENT at {first_vehicle.get('location')}!")
                        
                        vehicle_count = len(vehicles)

                        # --- FIXED: Building the Incident exactly according to your schemas.py ---
                        new_incident = Incident(
                            source="traffic", # Mandatory field in your schema
                            location=Location(
                                lat=6.9271, # Default placeholder coordinates
                                lng=79.8612, 
                                address=str(first_vehicle.get("location", "Unknown Location"))
                            ),
                            camera_risk_class="high", 
                            severity_grade="high",
                            accident=Accident(            # <-- FIXED NAME
                                vehicles_involved=vehicle_count,
                                fire_present=False 
                            ),
                            reported_at=datetime.utcnow().isoformat()
                        )
                        
                        prioritized_incident = score_incident(new_incident)
                        
                        await my_db["incidents"].insert_one(prioritized_incident.model_dump(exclude_none=True))
                    
                    else:
                        print(f"✅ AI checked {first_vehicle.get('location')} - No accident found. Ignoring.")

                # Mark as processed in friend's collection
                row_ids = [row["_id"] for row in new_rows]
                await friend_collection.update_many(
                    {"_id": {"$in": row_ids}},
                    {"$set": {"processed": True}}
                )

        except Exception as e:
            print(f"Background Worker Error: {e}")
            
        await asyncio.sleep(10)

def start_scheduler():
    loop = asyncio.get_event_loop()
    loop.create_task(process_shared_database())