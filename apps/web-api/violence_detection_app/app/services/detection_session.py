import cv2

from violence_detection_app.src.model_inference.action_recognition import ActionRecognition
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
        # Note: object_detector not initialized here anymore (using microservice)
        self.video_cap = None
        
    def initialize(self) -> bool:
        """Initialize LRCN model and open video"""
        try:
            # 1. Initialize LRCN model
            self.action_detector = ActionRecognition(
                model_path=config.LRCN_MODEL_PATH,
                confidence_threshold=config.LRCN_CONFIDENCE_THRESHOLD,
                sequence_length=config.SEQUENCE_LENGTH,
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
            print(f"❌ Error initializing session {self.session_id}: {e}")
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
            
        print(f"🧹 Session {self.session_id} cleaned up")
