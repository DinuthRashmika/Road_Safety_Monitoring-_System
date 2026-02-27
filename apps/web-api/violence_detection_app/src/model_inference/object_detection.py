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
        self.handler = VideoHandler()
        self.frame_extractor = FrameExtractor()

        # Colors for bounding boxes (BGR format for OpenCV)
        self.colors = {
            'knife': (0, 0, 255),      # Red
            'gun': (0, 165, 255),      # Orange
            'stick': (0, 255, 255)     # Yellow
        }

        # Load YOLO model
        self.yolo_model = self.load_yolo_model(self.model_path)

        if self.verbose:
            print(f"\nObjectDetection initialized")
            print(f"Model path: {self.model_path}")
            print(f"Confidence threshold: {self.confidence_threshold}")
            print(f"Detecting: {', '.join(self.violent_objects)}\n")


    def load_yolo_model(self, model_path):

        if self.verbose:
            print(f"----Loading YOLO Model----")
        
        try:
            from ultralytics import YOLO

            if model_path is None:
                model_path = config.YOLO_MODEL_PATH

            model = YOLO(model_path)
            
            if self.verbose:
                print(f"YOLO Model loaded successfully!")
                print(f"Model: {model_path}\n")

            return model
        
        except ImportError:
            if self.verbose:
                print(f"Ultralytics not installed.")
                print(f"  Install with: pip install ultralytics\n")
            return None
        
        except Exception as e:
            if self.verbose:
                print(f"Error loading YOLO: {e}\n") 
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


    def draw_detections_on_frame_test(self, frame, detections, frame_index=None):

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
            
            # Draw label text (white confidence)
            cv2.putText(
                display_frame,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),  # White text
                2
            )
        
        # Add frame info at top (frame_index and detections length on top left)
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
            warning_text = "VIOLENCE DETECTED!"
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
    


    def process_video_test(self, video_path, output_path=None, display=True):

        print("\n" + "="*70)
        print(f"PROCESSING VIDEO: {video_path}")
        print("="*70 + "\n")
        
        # Open video
        # cap = cv2.VideoCapture(video_path)
        cap = self.handler.read_video(video_path)
        
        if not cap.isOpened():
            print(f"Error: Cannot open video {video_path}")
            return None
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video Information:")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps}")
        print(f"  Total frames: {total_frames}")
        print(f"  Duration: {total_frames/fps:.1f}s\n")
        
        # Setup video writer
        video_writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            print(f"Output will be saved to: {output_path}\n")
        
        # Statistics
        stats = {
            'frames_processed': 0,
            'frames_with_detections': 0,
            'total_detections': 0,
            'detections_by_object': {},
            'total_objects_detected': [],
            'confidence_sums': {},
            'avg_confidences': {}
        }
        
        print("Processing frames...")
        if display:
            print("Press 'q' to quit early\n")
        
        frame_index = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                frame_index += 1
                stats['frames_processed'] += 1
                
                # ==========================================
                # DETECT OBJECTS IN THIS FRAME
                # ==========================================
                detections = self.detect_in_frame(frame)
                
                # Update statistics
                if len(detections) > 0:
                    stats['frames_with_detections'] += 1
                    stats['total_detections'] += len(detections)
                    
                    for det in detections:
                        obj_name = det['object']
                        confidence = det['confidence']
                        
                        stats['detections_by_object'][obj_name] = \
                            stats['detections_by_object'].get(obj_name, 0) + 1
                        
                        if obj_name not in stats['total_objects_detected']:
                            stats['total_objects_detected'].append(obj_name)

                        if obj_name in stats['confidence_sums']:
                            stats['confidence_sums'][obj_name] += confidence
                        else:
                            stats['confidence_sums'][obj_name] = confidence
                
                # ==========================================
                # DRAW DETECTIONS ON FRAME
                # ==========================================
                display_frame = self.draw_detections_on_frame_test(
                    frame, 
                    detections, 
                    frame_index
                )
                
                # ==========================================
                # SAVE FRAME (if output path provided)
                # ==========================================
                if video_writer:
                    video_writer.write(display_frame)
                
                # ==========================================
                # DISPLAY FRAME (if display enabled)
                # ==========================================
                if display:
                    cv2.imshow('Violence Detection - Object Detection', display_frame)
                    
                    # Check for 'q' key to quit
                    if cv2.waitKey(16) & 0xFF == ord('q'):
                        print("\n\nStopped by user")
                        break
                
                # Progress indicator
                if frame_index % 30 == 0:
                    progress = frame_index / total_frames * 100
                    print(f"Progress: {progress:.1f}% | Detections: {stats['total_detections']}", 
                          end='\r')

                # ==========================================
                # CALCULATE REMAINING STATS
                # ==========================================
                for obj_name, total_conf in stats['confidence_sums'].items():
                    count = stats['detections_by_object'].get(obj_name, 1)
                    stats['avg_confidences'][obj_name] = total_conf / count
        finally:
            # Cleanup
            cap.release()
            if video_writer:
                video_writer.release()
            cv2.destroyAllWindows()
        
        # Print final statistics
        print("\n\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        print(f"\nStatistics:")
        print(f"Total frames: {stats['frames_processed']}")
        print(f"Frames with detections: {stats['frames_with_detections']}")
        print(f"Total detections: {stats['total_detections']}")
        
        if stats['detections_by_object']:
            print(f"\nDetections by object:")
            for obj, count in sorted(stats['detections_by_object'].items()):
                print(f"   {obj:10s}: {count:4d}")
        
        if output_path:
            print(f"\nOutput saved to: {output_path}")
        
        print("\n" + "="*70 + "\n")
        
        return stats


    def process_webcam(self, camera_index=0, output_path=None):

        print("\n" + "="*70)
        print(f"PROCESSING WEBCAM (Camera {camera_index})")
        print("="*70)
        print("\nPress 'q' to quit\n")
        
        # Open webcam
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Error: Cannot open camera {camera_index}")
            return
        
        # Get properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 30  # Default for webcam
        
        # Setup video writer
        video_writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_index = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("❌ Failed to grab frame")
                    break
                
                frame_index += 1
                
                # Detect objects
                detections = self.detect_in_frame(frame, frame_index)
                
                # Draw detections
                display_frame = self.draw_detections_on_frame_test(
                    frame, 
                    detections, 
                    frame_index
                )
                
                # Save frame
                if video_writer:
                    video_writer.write(display_frame)
                
                # Display
                cv2.imshow('Violence Detection - Live', display_frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nStopped by user")
                    break
        
        finally:
            cap.release()
            if video_writer:
                video_writer.release()
            cv2.destroyAllWindows()
        
        print(f"\nProcessed {frame_index} frames")
        if output_path:
            print(f"Output saved to: {output_path}")


    def save_frame_with_detections(self, frame: np.ndarray, detections: List[Dict], output_path: str, frame_index: int = None):

        # Draw detections on frame
        display_frame = self.draw_detections_on_frame_test(frame, detections, frame_index)
        
        # Save
        cv2.imwrite(output_path, display_frame)
        
        if self.verbose:
            print(f"Saved frame to: {output_path}")


if __name__ == "__main__":

    print("\n" + "="*70)
    print("OBJECT DETECTION - TEST")
    print("="*70)
    
    # Initialize detector
    detector = ObjectDetection(
        model_path=config.YOLO_MODEL_PATH, 
        confidence_threshold=0.25,
        verbose=True
    )
    
    # Testttttt Process video file
    stats = detector.process_video_test(
        video_path=config.VIDEO_PATH,
        output_path=config.OUTPUT_DIR + '/yolo_output_demo.mp4',
        display=True  # Show video while processing
    )
    
    # Process webcam
    # detector.process_webcam(
    #     camera_index=0,
    #     output_path='webcam_output.mp4'
    # )
    
    # Process single frame
    # frame = cv2.imread('test_image.jpg')
    # detections = detector.detect_in_frame(frame)
    # detector.save_frame_with_detections(
    #     frame, 
    #     detections, 
    #     'output_frame.jpg'
    # )
    
    print("\n✓ Done!")


















# import sys
# import traceback
# from typing import Dict, List
# import cv2
# import numpy as np
# from violence_detection_app.src.config import config
# from violence_detection_app.src.data_processing.video_handler import VideoHandler
# from violence_detection_app.src.data_processing.frame_extractor import FrameExtractor
# from violence_detection_app.src.data_processing import frame_extractor
# from ultralytics import YOLO

# class ObjectDetection:

#     def __init__(self, model_path=None, confidence_threshold=None, verbose=True):
#         self.model_path = model_path or config.YOLO_MODEL_PATH
#         self.confidence_threshold = confidence_threshold or config.YOLO_CONFIDENCE_THRESHOLD
#         self.verbose = verbose

#         self.handler = VideoHandler()
#         self.frame_extractor = FrameExtractor()

#         self.violent_objects = config.VIOLENT_OBJECTS

#         self.colors = {
#             'knife': (0, 0, 255),      # Red
#             'gun': (0, 165, 255),      # Orange
#             'stick': (0, 255, 255)     # Yellow
#         }

#         self.yolo_model = self.load_yolo_model(model_path)

#         print(f"Model Path from Parameters: {model_path}")
#         print(f"Model Path from self.model_path: {self.model_path}")


#     def load_yolo_model(self, model_path):

#         if self.verbose:
#             print(f"----Loading YOLO Model----")
        
#         try:
#             from ultralytics import YOLO

#             if model_path is None:
#                 model_path = config.YOLO_MODEL_PATH

#             model = YOLO(model_path)
#             print(f"YOLO Model Loaded!")

#             return model
        
#         except ImportError:
#             if self.verbose:
#                 print(f"Ultralytics not installed. Using default model")
#             return None
#         except Exception as e:
#             if self.verbose:
#                 print(f"Error loading YOLO {e}") 
#             return None       
        
    
#     def detect_in_frame(self, frame):
        
#         detections = []

#         # For each frame
#         results = self.yolo_model.predict(
#             frame,
#             conf = self.confidence_threshold,
#             verbose = False
#         ) 

#         # Extract detections for each frame
#         for result in results:
#             for box in result.boxes: #multiple bboxes
                
#                 class_id = int(box.cls)
#                 class_name = result.names[class_id]
#                 confidence = float(box.conf)
#                 bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
#                 # Check if it's a violent object
#                 if class_name.lower() in [obj.lower() for obj in self.violent_objects]:
#                     detections.append({
#                         'object': class_name.lower(),
#                         'confidence': confidence, # we are sending this now
#                         'bbox': bbox,
#                         'class_id': class_id
#                     })
        
#         return detections  # for each frame
    

#     def draw_detections_on_frame(self, frame, detections, frame_index=None):

#         # Make a copy to draw on (don't modify original)
#         display_frame = frame.copy()
        
#         # Draw each detection
#         for detection in detections:
#             obj_name = detection['object']
#             confidence = detection['confidence']
#             bbox = detection['bbox']
            
#             # Convert bounding box to integers
#             x1, y1, x2, y2 = map(int, bbox)
            
#             # Choose color for this object
#             color = self.colors.get(obj_name, (0, 255, 0))  # Default: green
            
#             # Draw bounding box (thick rectangle)
#             cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
            
#             # Prepare label text
#             label = f"{obj_name.upper()} {confidence:.2%}"
            
#             # Measure label size, so the text doesnot overlap the video
#             (label_width, label_height), baseline = cv2.getTextSize(
#                 label, 
#                 cv2.FONT_HERSHEY_SIMPLEX, 
#                 0.7, 
#                 2
#             )
            
#             # Draw label background (filled rectangle)
#             cv2.rectangle(
#                 display_frame,
#                 (x1, y1 - label_height - 10),
#                 (x1 + label_width + 10, y1),
#                 color,
#                 -1  # Filled
#             )
            
#             # Draw label text (white) On top of colored rectangle
#             cv2.putText(
#                 display_frame,
#                 label,
#                 (x1 + 5, y1 - 5),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.7,
#                 (255, 255, 255),  # White text
#                 2
#             )
        
#         # Add frame info at top
#         if frame_index is not None:
#             info_text = f"Frame: {frame_index} | Detections: {len(detections)}"
#         else:
#             info_text = f"Detections: {len(detections)}"
        
#         cv2.putText(
#             display_frame,
#             info_text,
#             (10, 35),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             1.0,
#             (0, 255, 0),  # Green
#             2
#         )
        
#         # Add warning if violent objects detected
#         if len(detections) > 0:
#             warning_text = "VIOLENCE DETECTED!"
#             cv2.putText(
#                 display_frame,
#                 warning_text,
#                 (10, 75),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 1.2,
#                 (0, 0, 255),  # Red
#                 3
#             )
        
#         return display_frame # One frame with drawings (numpy array). Input frame was also a numpy array right? 
#                              # frame includes confidence, bbox drawn and a warining message is drawn
    
    
#     def display_frame(self, display_frame, key_to_stop):

#         cv2.imshow('Violence Detection - Streaming', display_frame)
                    
#         # Check for 'q' key to quit
#         if cv2.waitKey(1) & 0xFF == ord(key_to_stop):
#             print("\nStopped by user")


#     def process_video_for_object_detection(self, video_source, output_path=None, display=True):

#         print("----Object Detection Started----")
#         cap = self.handler.read_video(video_source)

#         video_properties = self.handler.get_video_properties(video_source)
#         print(f"Incoming video FPS: {video_properties['fps']}")

#         # video_writer = None
#         # if output_path:
#         #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#         #     video_writer = cv2.VideoWriter(output_path, fourcc, video_properties['fps'], (video_properties['width'], video_properties['height']))
#         #     print(f"Output will be saved to: {output_path}\n")

#         stats = {
#             'frames_processed': 0,
#             'frames_with_detections': 0,
#             'total_detections': 0,
#             'detections_by_object': {}
#         }
        
#         try:
#             for frame_index, frame in self.frame_extractor.extract_each_frame(video_source):

#                 # detect for one frame
#                 stats['frames_processed'] += 1
#                 detections = self.detect_in_frame(frame)

#                 # if detections are there 
#                 if len(detections) > 0: # update stats
#                     stats['frames_with_detections'] += 1
#                     stats['total_detections'] += len(detections)

#                     # for each detection in detections[]
#                     for det in detections:
#                         obj_name = det['object']
#                         stats['detections_by_object'][obj_name] = \
#                             stats['detections_by_object'].get(obj_name, 0) + 1
                        
#                 # draw detections on one frame
#                 display_frame = self.draw_detections_on_frame(frame, detections, frame_index)

#                 # if save frame
#                 # if video_writer:
#                 #     video_writer.write(display_frame)

#                 # if display frame
#                 if display:
#                     cv2.imshow('Violence Detection - Object Detection Streaming', display_frame)

#                     # Check for 'q' key to quit
#                     if cv2.waitKey(1) & 0xFF == ord('q'):
#                         print("\n\nStopped by user")
#                         break

#                 # progress indicator
#                 if frame_index % 30 == 0:
#                     progress = frame_index / video_properties['frame_count'] * 100
#                     print(f"Progress: {progress:.1f}% | Detections: {stats['total_detections']}",
#                         end='\r')
                    
#         except Exception as e:
#             print(f"❌ Error: {e}")
#             traceback.print_exc()
#         finally:
#             cap.release()
#             # if video_writer:
#             #     video_writer.release()
#             cv2.destroyAllWindows()
        
#         # Print final statistics
#         print("----Object Detection Completed----")
#         print(f"\nStatistics:")
#         print(f"Total frames: {stats['frames_processed']}")
#         print(f"Frames with detections: {stats['frames_with_detections']}")
#         print(f"Total detections: {stats['total_detections']}")
        
#         print(f"\n----Printing Object Detection Statistics----")
#         if stats['detections_by_object']:
#             for obj, count in sorted(stats['detections_by_object'].items()):
#                 print(f"   {obj:10s}: {count:4d}")
        
#         if output_path:
#             print(f"\n💾 Output saved to: {output_path}")
        
#         print("\n" + "="*70 + "\n")
        
#         return stats
    

#     def save_frame_with_detections(self, frame: np.ndarray, detections: List[Dict], output_path: str, frame_index: int = None):

#         # Draw detections on frame
#         display_frame = self.draw_detections_on_frame(frame, detections, frame_index)
        
#         # Save the one frame with detections
#         cv2.imwrite(output_path, display_frame)
        
#         if self.verbose:
#             print(f"💾 Saved frame to: {output_path}")
                

# if __name__ == "__main__":

#     object_detector = ObjectDetection()

#     stats = object_detector.process_video_for_object_detection(config.VIDEO_PATH, config.OUTPUT_DIR + '/shooting_test_1_yolo_result', display=True)
#     print(f"----Object Detection Ended!")



