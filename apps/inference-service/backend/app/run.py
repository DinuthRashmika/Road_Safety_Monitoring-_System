#!/usr/bin/env python3
"""
Simple script to run the plate detector with webcam.
"""
import cv2
import numpy as np
import base64
import requests
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.plate_detector import PlateDetector

def main():
    """Main function to run plate detector with webcam"""
    print("=" * 50)
    print("Road Safety System - Plate Detector")
    print("=" * 50)
    
    # Initialize detector
    detector = PlateDetector()
    
    # Load model
    if not detector.load_model():
        print("Failed to load model. Exiting.")
        return
    
    # Open webcam
    cap = cv2.VideoCapture(0)  # 0 for default webcam
    if not cap.isOpened():
        print("Failed to open webcam")
        return
    
    print("\nPlate detection started. Press 'q' to quit.")
    print("Detected plates will be sent to the API server.")
    
    frame_count = 0
    api_url = "http://localhost:8000/api/violations/detect"
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            frame_count += 1
            
            # Process every 5th frame for performance
            if frame_count % 5 != 0:
                continue
            
            # Detect plate
            result = detector.detect_plate(frame)
            
            if result:
                plate_number, confidence, bbox, annotated_frame = result
                
                print(f"\n🚗 Detected: {plate_number} (confidence: {confidence:.2f})")
                
                # Convert frame to base64
                _, buffer = cv2.imencode('.jpg', frame)
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Send to API
                try:
                    payload = {
                        "plate_number": plate_number,
                        "confidence": float(confidence),
                        "image_base64": image_base64,
                        "location": "Main Entrance",
                        "camera_id": "WEBCAM_001"
                    }
                    
                    response = requests.post(api_url, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            if data.get("vehicle_owner"):
                                owner = data["vehicle_owner"]
                                print(f"   👤 Owner: {owner['name']}")
                                print(f"   📞 Phone: {owner['phone']}")
                                print(f"   📧 Email: {owner['email']}")
                            else:
                                print("   ℹ️ No registered owner found")
                        else:
                            print(f"   ❌ API error: {data.get('message')}")
                    else:
                        print(f"   ❌ API request failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Failed to send to API: {e}")
            
            # Show frame
            cv2.imshow('Plate Detector', frame if result is None else annotated_frame)
            
            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Small delay
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n✅ Plate detector stopped")

if __name__ == "__main__":
    main()