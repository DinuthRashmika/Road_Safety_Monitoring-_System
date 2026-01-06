import cv2

from violence_detection_app.src.model_inference.action_recognition import ActionRecognition
# from violence_detection_app.src.model_inference.object_detection import ObjectDetection
from violence_detection_app.src.model_fusion.model_stats import ModelStatistics
from violence_detection_app.src.config import config


class DetectionSession:
    """ 
    Manages a single detection session. one video, one model, one state
    It represents a single video + model + state.
    how do initialize this session?
    It does NOT know about other sessions.
    """
    
    def __init__(self, session_id: str, source_path: str):
        self.session_id = session_id
        self.source_path = source_path
        self.is_active = False
        self.should_stop = False

        self.action_detector = None
        self.object_detector = None
        self.video_cap = None
        
    def initialize(self) -> bool:
        """for now Initialize LRCN only method when initializing the session"""
        try:
            # 1. Initialize model LRCN
            self.action_detector = ActionRecognition(
                model_path=config.LRCN_MODEL_PATH,
                confidence_threshold=config.LRCN_CONFIDENCE_THRESHOLD,
                sequence_length=config.SEQUENCE_LENGTH,
                verbose=False
            )

            # 2. Initialize YOLO model
            # self.object_detector = ObjectDetection(
            #     model_path = config.YOLO_MODEL_PATH,
            #     confidence_threshold = config.YOLO_CONFIDENCE_THRESHOLD,
            #     sequence_length=config.SEQUENCE_LENGTH,
            #     verbose = False #silent execution in service and debuggable in src (Verbose by default - True)
            # )
            
            # 3. Open video
            self.video_cap = cv2.VideoCapture(self.source_path)
            
            if not self.video_cap.isOpened():
                raise Exception(f"Cannot open video source: {self.source_path}")
            
            # If anything goes wrong session is not stored in session list
            # Session is waiting for a WebSocket client
            self.is_active = True
            return True
            
        except Exception as e:
            print(f"Error initializing session {self.session_id}: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_active = False
        if self.video_cap:
            self.video_cap.release()
        if self.action_detector:
            self.action_detector.reset_buffer()

    def stop(self):
        self.should_stop = True 
