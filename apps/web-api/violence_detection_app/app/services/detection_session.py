import cv2

from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch
from violence_detection_app.src.model_inference.object_detection import ObjectDetection
from violence_detection_app.src.config import config


class DetectionSession:
    """ 
    Manages a single detection session: one video, one model, one state
    """
    
    def __init__(self, session_id: str, source_path: str):
        self.session_id = session_id
        self.source_path = source_path
        self.is_active = False
        self.should_stop = False  # Flag to stop processing
        
        self.action_detector = None
        self.object_detector = None
        self.video_cap = None
        
    def initialize(self) -> bool:
        """Initialize LRCN model and open video"""
        try:
            # 1. Initialize LRCN model
            self.action_detector = ActionRecognitionTorch(
                model_path=config.LRCN_TORCH_MODEL_PATH,
                confidence_threshold=config.LRCN_CONFIDENCE_THRESHOLD,
                sequence_length=config.SEQUENCE_LENGTH,
                verbose=False
            )

            # 1. Initialize YOLO model (if needed)
            self.object_detector = ObjectDetection(
                model_path=config.YOLO_MODEL_PATH, 
                confidence_threshold=config.YOLO_CONFIDENCE_THRESHOLD, 
                verbose=False
            )
            
            # 2. Open video
            self.video_cap = cv2.VideoCapture(self.source_path)
            
            if not self.video_cap.isOpened():
                raise Exception(f"Cannot open video source: {self.source_path}")
            
            self.is_active = True
            self.should_stop = False
            
            print(f" Session {self.session_id} initialized")
            print(f"   Source: {self.source_path}")
            
            return True
            
        except Exception as e:
            print(f" Error initializing session {self.session_id}: {e}")
            return False
    
    def stop(self):
        """Request to stop processing"""
        self.should_stop = True
        print(f"⏹️ Stop requested for session {self.session_id}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_active = False
        self.should_stop = True
        
        if self.video_cap:
            self.video_cap.release()
            
        if self.action_detector:
            self.action_detector.reset_buffer()

        # if self.object_detector:
        #     self.object_detector.cleanup()
            
        print(f"🧹 Session {self.session_id} cleaned up")
