import sys
from typing import Dict, List, Optional
import cv2
import numpy as np
from violence_detection_app.src.config import config
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.src.data_processing.frame_extractor import FrameExtractor
from violence_detection_app.src.data_processing import frame_extractor
from ultralytics import YOLO

class ObjectDetection:

    def __init__(self, model_path=None, confidence_threshold=None, verbose=True):

        self.model_path = model_path or config.YOLO_MODEL_PATH
        self.confidence_threshold = confidence_threshold or config.YOLO_CONFIDENCE_THRESHOLD
        self.verbose = verbose

        # Violent objects to detect
        self.violent_objects = config.VIOLENT_OBJECTS

        # Colors for bounding boxes (BGR format for OpenCV)
        self.colors = {
            'knife': (0, 0, 255),      # Red
            'gun': (0, 165, 255),      # Orange
            'stick': (0, 255, 255)     # Yellow
        }

        # Load YOLO model
        self.yolo_model = self.load_yolo_model(self.model_path)

        if self.verbose:
            print(f"\n✓ ObjectDetection initialized")
            print(f"  Model path: {self.model_path}")
            print(f"  Confidence threshold: {self.confidence_threshold}")
            print(f"  Detecting: {', '.join(self.violent_objects)}\n")


    def load_yolo_model(self, model_path):

        if self.verbose:
            print(f"----Loading YOLO Model----")
        
        try:
            from ultralytics import YOLO

            if model_path is None:
                model_path = config.YOLO_MODEL_PATH

            model = YOLO(model_path)
            
            if self.verbose:
                print(f"✓ YOLO Model loaded successfully!")
                print(f"  Model: {model_path}\n")

            return model
        
        except ImportError:
            if self.verbose:
                print(f"⚠ Ultralytics not installed.")
                print(f"  Install with: pip install ultralytics\n")
            return None
        
        except Exception as e:
            if self.verbose:
                print(f"⚠ Error loading YOLO: {e}\n") 
            return None       
        

    def detect_in_frame(self, frame):

        detections = []

        if self.yolo_model is None:
            return detections

        # Run YOLO prediction
        results = self.yolo_model.predict(
            frame,
            conf=self.confidence_threshold,
            verbose=False
        ) 

        # Extract detections
        for result in results:
            for box in result.boxes:
                
                class_id = int(box.cls)
                class_name = result.names[class_id]
                confidence = float(box.conf)
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                # Check if it's a violent object
                if class_name.lower() in [obj.lower() for obj in self.violent_objects]:
                    detections.append({
                        'object': class_name.lower(),
                        'confidence': confidence,
                        'bbox': bbox,
                        'class_id': class_id
                    })
        
        return detections


    def draw_detections_on_frame(self, frame, detections, frame_index=None):

        # Make a copy to draw on
        display_frame = frame.copy()
        
        # Draw each detection
        for detection in detections:
            obj_name = detection['object']
            confidence = detection['confidence']
            bbox = detection['bbox']
            
            # Convert bounding box to integers
            x1, y1, x2, y2 = map(int, bbox)
            
            # Choose color for this object
            color = self.colors.get(obj_name, (0, 255, 0))  # Default: green
            
            # Draw bounding box (thick rectangle)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
            
            # Prepare label text
            label = f"{obj_name.upper()} {confidence:.2%}"
            
            # Measure label size
            (label_width, label_height), baseline = cv2.getTextSize(
                label, 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                2
            )
            
            # Draw label background (filled rectangle)
            cv2.rectangle(
                display_frame,
                (x1, y1 - label_height - 10),
                (x1 + label_width + 10, y1),
                color,
                -1  # Filled
            )
            
            # Draw label text (white)
            cv2.putText(
                display_frame,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),  # White text
                2
            )
        
        # Add frame info at top
        if frame_index is not None:
            info_text = f"Frame: {frame_index} | Detections: {len(detections)}"
        else:
            info_text = f"Detections: {len(detections)}"
        
        cv2.putText(
            display_frame,
            info_text,
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),  # Green
            2
        )
        
        # Add warning if violent objects detected
        if len(detections) > 0:
            warning_text = "⚠ VIOLENCE DETECTED!"
            cv2.putText(
                display_frame,
                warning_text,
                (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 255),  # Red
                3
            )
        
        return display_frame

