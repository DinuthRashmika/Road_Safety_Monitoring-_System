import os
import sys
from typing import Dict, List
import cv2
import numpy as np
from violence_detection_app.src.config import config
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.src.data_processing.frame_extractor import FrameExtractor
from violence_detection_app.src.data_processing import frame_extractor
from ultralytics import YOLO
from collections import deque

class ObjectDetec2:

    def __init__(self, model_path=None, confidence_threshold=None, verbose=True):

        self.model_path = model_path or config.YOLO_MODEL_PATH
        self.confidence_threshold = confidence_threshold or config.YOLO_CONFIDENCE_THRESHOLD
        self.verbose = verbose

        self.violent_objects = config.VIOLENT_OBJECTS
        self.handler = VideoHandler()
        self.frame_extractor = FrameExtractor()

        self.colors = {
            'knife': (0, 0, 255),      # Red
            'gun': (0, 165, 255),      # Orange
            'stick': (0, 255, 255)     # Yellow
        }

        self.yolo_model = self.load_yolo_model(model_path)

        self.window_size = 30
        self.alert_threshold = 0.3 # Alert if knife in >30% of window

        print("----Starting Object Detection Service----")


    def load_yolo_model(self, model_path):

        if self.verbose:
            print(f"----Loading YOLO Model----")
        
        try:
            from ultralytics import YOLO

            if model_path is None:
                model_path = config.YOLO_MODEL_PATH

            model = YOLO(model_path)
            print(f"YOLO Model Loaded!")

            return model
        
        except ImportError:
            if self.verbose:
                print(f"Ultralytics not installed. Using default model")
            return None
        except Exception as e:
            if self.verbose:
                print(f"Error loading YOLO {e}") 
            return None  


    # Statistics for current window
    def initialize_current_window_stats(self):
        stats = {}
        for obj in self.violent_objects:
            stats[obj] = {
                'frames_present': 0,
                'confidences': [],
                'avg_confidence': 0.0,
                'presence_rate': 0.0
            }
        return stats
    

    def detect_in_frame(self, frame):
        
        detections = []

        # For each frame
        results = self.yolo_model.predict(
            frame,
            conf = self.confidence_threshold,
            verbose = False
        ) 

        # Extract detections for each frame
        for result in results:
            for box in result.boxes: #multiple bboxes
                
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

        # Make a copy to draw on (don't modify original)
        display_frame = frame.copy()
        
        # Draw each detection
        for detection in detections:
            obj_name = detection['object']
            confidence = detection['confidence']
            bbox = detection['bbox']
            
            # Get coordinates
            x1, y1, x2, y2 = map(int, bbox)
            
            # Get color for this object
            color = self.colors.get(obj_name, (0, 255, 0))  # Default: green
            
            # Draw bounding box (thick rectangle)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
            
            # Prepare label text
            label = f"{obj_name.upper()} {confidence:.2%}"
            
            # Calculate label background size
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
        
        return display_frame # Frame with drawings (numpy array). Input frame was also a numpy array right?
    

    def process_video_stream(self, video_source, display=True, save_output=None):

        """
        Process CONTINUOUS CCTV stream with real-time alerts
        
        Key differences from batch processing:
        1. Uses SLIDING WINDOW instead of total frames
        2. Gives IMMEDIATE ALERTS instead of waiting for end
        3. Reports CURRENT THREAT instead of overall percentage
        
        Args:
            video_source: RTSP stream URL or camera index (0 for webcam)
            display: Show live video
            save_output: Save alerts to video
        """
        # Sliding window Buffer
        window_buffer = deque(maxlen=self.window_size)

        # Each window Statistics
        window_stats = self.initialize_current_window_stats()

        # Statistics for all
        overall_stats = {
            'total_frames_processed': 0,
            'total_alerts': 0,
            'objects_detected_ever': set()
        }
        
        # Video writer for saving output
        video_writer = None

        print("----Object Detection Started----")
        print(f"Window Size: {self.window_size} frames")
        print(f"Alert Threshold: {self.alert_threshold*100:.0f}%")
        print(f"Press 'q' to stop")
        
        try:
            # Process each frame from stream
            for frame_index, frame in self.frame_extractor.extract_each_frame(video_source):
                
                # Step 1: Detect objects in this frame
                detections = self.detect_in_frame(frame)

                # Step 2. Add to sliding window
                window_buffer.append({
                    'frame_index': frame_index,
                    'detections': detections
                })
                
                # Step 3. Update overall stats
                overall_stats['total_frames_processed'] += 1
                if detections:
                    for det in detections:
                        overall_stats['objects_detected_ever'].add(det['object'])
                
                # Step 4. Analyze CURRENT WINDOW (not entire stream)
                threat_analysis = self.analyze_current_window(window_buffer)
                
                # # Step 5. Check for alerts and display (if needed)
                # alert = self._check_for_alert(threat_analysis)

                # if alert:
                #     self._display_alert(alert, frame_index)
                #     overall_stats['total_alerts'] += 1
                
                # Draw bounding boxes on frame
                display_frame = self.draw_detections_on_frame(
                    frame, 
                    detections, 
                    frame_index
                )

                # Add window statistics to frame
                display_frame = self.add_window_stats_to_frame(
                    display_frame, 
                    threat_analysis,
                    frame_index
                )

                # Step 4: Display frame (if enabled)
                if display:
                    cv2.imshow('Violence Detection - Streaming', display_frame)
                    
                    # Check for 'q' key to quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nStopped by user")
                        break
                
                # Step 5: Save to output video (if enabled)
                if save_output:
                    if video_writer is None:
                        # Initialize video writer on first frame
                        height, width = display_frame.shape[:2]
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        video_writer = cv2.VideoWriter(
                            save_output, 
                            fourcc, 
                            40,  # FPS should match videos original FPS
                            (width, height)
                        )
                    video_writer.write(display_frame)

                # Old frames automatically removed from window buffer
                #     (deque with maxlen does this automatically)
            
            print("----Object Detection Ended----")
            

        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
        
        finally:
            # Cleanup
            if display:
                cv2.destroyAllWindows()
            if video_writer:
                video_writer.release()
                print(f"💾 Alert video saved to: {save_output}")
            
            # Print summary
            self.print_session_summary(overall_stats)


def main():
    # Configuration
    MODEL_PATH = config.YOLO_MODEL_PATH # Update this
    VIDEO_PATH = config.VIDEO_PATH # Update this
    OUTPUT_PATH = config.OUTPUT_DIR  # Where to save results
    
    print("="*70)
    print("VIOLENCE DETECTION TEST")
    print("="*70)
    print(f"Video: {VIDEO_PATH}")
    print(f"Model: {MODEL_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print("="*70)
    print("\nPress 'q' to stop processing")
    print("="*70 + "\n")
    
    # Initialize detector
    detector = ObjectDetec2(
        model_path=MODEL_PATH,
        confidence_threshold=0.5,  # Adjust as needed
        verbose=True
    )
    
    # Process the video
    try:
        detector.process_video_stream(
            video_source=VIDEO_PATH,
            display=True,           # Show live video window
            save_output=OUTPUT_PATH # Save annotated video
        )
        
        print("\nProcessing complete!")
        print(f"Check output at: {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        detector.clean_memory()

if __name__ == "__main__":
    main()

