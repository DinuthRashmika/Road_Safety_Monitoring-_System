from typing import Dict
from violence_detection_app.src.model_inference.object_detection import ObjectDetection
from violence_detection_app.src.model_inference.action_recognition import ActionRecognition
from violence_detection_app.src.config import config

class ModelFusion:

    def __init__(self):
        self.object_detector = ObjectDetection()
        self.action_detector = ActionRecognition()

        self.object_weights = config.OBJECT_WEIGHTS
        self.action_weights = config.ACTION_WEIGHTS
        self.object_detection_weight = config.OBJECT_DETECTION_WEIGHT # YOLO contributes 40%
        self.action_recognition_weight = config.ACTION_RECOGNITION_WEIGHT  # LRCN contributes 60%

        print("----Model Results Fusion Starting----")
    
    def lrcn_weighted_score(self, lrcn_result: Dict) -> Dict:

        if not lrcn_result.get('ready', False):
            return 0.0
        
        action = lrcn_result["action"]
        lrcn_confidence = lrcn_result["confidence"]
        # action = lrcn_result.get('action', 'Unknown')
        # lrcn_confidence = lrcn_result.get('confidence', 0.0)

        lrcn_weight = lrcn_confidence * self.action_weights[action]
        # lrcn_weight = self.action_weights.get(action)

        # Clip to [0, 1]
        lrcn_weight = min(lrcn_weight, 1.0)

        return lrcn_weight
    
    def yolo_weighted_score(self, yolo_result: Dict) -> Dict:
        
        yolo_detections = yolo_result.get('detections', [])
        
        if not yolo_detections:
            return 0.0

        max_weighted = 0.0
        
        for det in yolo_detections:
            object_name = det.get('object', '')
            confidence = det.get('confidence', 0.0)
            
            # Get object weight
            object_weight = self.object_weights.get(object_name, 1.0)
            
            # Calculate weighted confidence
            weighted = confidence * object_weight
            
            # Keep highest
            max_weighted = max(max_weighted, weighted)
        
        # Clip to [0, 1]
        max_weighted = min(max_weighted, 1.0)
        
        return max_weighted


    def combine_results(self, yolo_result: Dict, lrcn_result: Dict) -> Dict:

        # Calculate individual weighted scores
        lrcn_raw_score = self.object_detection_weight(yolo_result)
        yolo_raw_score = self.action_recognition_weight(lrcn_result)
        
        # Apply overall weights (YOLO 40%, LRCN 60%)
        yolo_contribution = yolo_raw_score * self.object_detection_weight
        lrcn_contribution = lrcn_raw_score * self.action_recognition_weight

        threat_score = yolo_contribution + lrcn_contribution

        if threat_score >= 0.8:
            threat_level = "CRITICAL"
        elif threat_score >= 0.6:
            threat_level = "HIGH"
        elif threat_score >= 0.4:
            threat_level = "MEDIUM"
        elif threat_score >= 0.2:
            threat_level = "LOW"
        else:
            threat_level = "NONE"


    







    
    