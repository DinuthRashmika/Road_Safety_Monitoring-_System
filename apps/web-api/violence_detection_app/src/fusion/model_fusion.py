from typing import Dict
from violence_detection_app.src.model_inference.object_detection import ObjectDetection
from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch
from violence_detection_app.src.config import config


# for each frame - for each lrcn result, for each yolo result per frame
class ModelFusion:

    def __init__(self, object_detection_weight=None, action_recognition_weight=None):
        self.object_detector = ObjectDetection()
        self.action_detector = ActionRecognitionTorch()

        self.object_weights = config.OBJECT_WEIGHTS
        self.action_weights = config.ACTION_WEIGHTS
        self.object_detection_weight = object_detection_weight or config.OBJECT_DETECTION_WEIGHT # YOLO contributes 40%
        self.action_recognition_weight = action_recognition_weight or config.ACTION_RECOGNITION_WEIGHT  # LRCN contributes 60%

        print("----Model Results Fusion Starting----")
    
    def calculate_lrcn_threat_score(self, lrcn_result: Dict) -> Dict:

        print(f"----LRCN weight calculation")
        if not lrcn_result.get('ready', False):
            return 0.0
        
        print(f"Action Weights: {config.ACTION_WEIGHTS}")

        if lrcn_result['ready'] and lrcn_result['is_violent']:

            action = lrcn_result.get('action', 'Unknown')
            print(f"current action: {action}")
            lrcn_confidence = lrcn_result.get('confidence', 0.0)
            print(f"current confidence lrcn: {lrcn_confidence}")

            # action weight
            action_weight = self.action_weights.get(action, 1.0)
            print(f"action weight for current action - {action} is {action_weight}")

            # add action weight
            action_score = lrcn_confidence * action_weight

            # clip betwenn 0,1
            action_score = min(action_score, 1.0)
            print(f"final action score: {action_score}")
            print(f"----lrcn ended")

        return action_score


    def calculate_yolo_threat_score(self, yolo_result: Dict) -> Dict:
        
        print(f"----YOLO weight calculation")

        yolo_detections = yolo_result.get('detections', [])
        
        if not yolo_detections:
            return 0.0
    
        max_score = 0.0
        
        for det in yolo_detections:
            object_name = det.get('object', '')
            print(f"current obj name: {object_name}")
            yolo_confidence = det.get('confidence', 0.0)
            print(f"current confidence yolo: {yolo_confidence}")
            
            # object weight
            object_weight = self.object_weights.get(object_name, 0.0)
            print(f"object weight for current object: {object_weight}")
            
            # add object weight
            object_score = yolo_confidence * object_weight
            
            # Keep highest
            max_score = max(max_score, object_score)
        
        # Clip to [0, 1]
        max_score = min(max_score, 1.0)
        print(f"final object score: {max_score}")
        print(f"----yolo ended")
        
        return max_score


    def classify_threat_score(self, threat_score):

        if threat_score >= 0.8:
            weight_level = "CRITICAL"
        elif threat_score >= 0.6:
            weight_level = "HIGH"
        elif threat_score >= 0.4:
            weight_level = "MEDIUM"
        elif threat_score >= 0.3:
            weight_level = "VERY LOW"
        else:
            weight_level = "NONE"

        return weight_level
    
    def synergy_bonus_calculation(self, threat_score, lrcn_result=dict, yolo_result=dict) -> float:

        print(f"snergy lrcn result: {lrcn_result}")
        print(f"snergy yolo result: {yolo_result}")
        print(f"snergy threat score : {threat_score}")

        for det in yolo_result.get('detections', []):
            obj = det.get('object', '')

            if lrcn_result.get('action', '') == 'shooting' and obj == 'gun':
                threat_score += 0.8
            if lrcn_result.get('action', '') == 'fighting' and obj == 'gun':
                threat_score += 0.7
            if lrcn_result.get('action', '') == 'fighting' and obj == 'stick':
                threat_score += 0.6
            if lrcn_result.get('action', '') == 'running' and obj == 'gun':
                threat_score += 0.7
            if lrcn_result.get('action', '') == 'running' and obj == 'stick':
                threat_score += 0.4
            if lrcn_result.get('action', '') == 'fighting' and obj == 'knife':
                threat_score += 0.7
            if lrcn_result.get('action', '') == 'running' and obj == 'knife':
                threat_score += 0.6
            if lrcn_result.get('action', '') == 'attacking' and obj == 'knife':
                threat_score += 0.8
            if lrcn_result.get('action', '') == 'fighting' and obj == 'stick':
                threat_score += 0.4
        
        threat_score = min(threat_score, 1.0)

        return threat_score
    

    def combine_results(self, yolo_result: Dict, lrcn_result: Dict) -> Dict:

        print("----Cmbine both----")

        # Calculate individual weighted scores
        object_score = self.calculate_yolo_threat_score(yolo_result)
        print(f"OBJECT SCORE: {object_score}")
        action_score = self.calculate_lrcn_threat_score(lrcn_result)
        print(f"ACTION SCORE: {action_score}")
        
        # Apply overall weights (YOLO 40%, LRCN 60%)
        yolo_contribution = object_score * self.object_detection_weight #40
        lrcn_contribution = action_score * self.action_recognition_weight #60

        # model total score
        total_threat_score = yolo_contribution + lrcn_contribution
        threat_score = min(total_threat_score, 100.0)
        print(f"total threat score: {threat_score}")

        # ----Bonus: 1. Synergy BOnuses
        threat_score = self.synergy_bonus_calculation(threat_score, lrcn_result, yolo_result)
        print(f"1. snergy threat score {threat_score}")

        # ----Bonus: 2. Multiple people + violent action
        # person_count = sum(1 for obj in yolo_result['objects'] if obj['class'] == 'person')
        # if person_count >= 2 and lrcn_result.get('is_violent', False):
        #     score += 10  # Bonus for group violence

        # ----Bonus: 3. threat level
        weight_level = self.classify_threat_score(threat_score)
        print(f"3. threat level {weight_level}")

        return {
            'threat_score': threat_score, # 0.80
            'weight_level': weight_level # combined score is HIGH
        }
            


        
# if __name__ == "__main__":
    
#     fusion = ModelFusion()

#     # Fake YOLO output
#     yolo_result = {
#         'detections': [
#             {
#                 'object': 'knife',
#                 'confidence': 0.72,
#                 'bbox': [100, 100, 200, 200],
#                 'class_id': 43
#             },
#             {
#                 'object': 'stick',
#                 'confidence': 0.60,
#                 'bbox': [50, 50, 120, 120],
#                 'class_id': 44
#             }
#         ]
#     }

#     # Fake LRCN output
#     lrcn_result = {
#         'action': 'fighting',
#         'confidence': 0.85,
#         'ready': True,
#         'all_probabilities': {},
#         'is_violent': True
#     }

#     result = fusion.combine_results(yolo_result, lrcn_result)

#     print("\n----FINAL RESULT")
#     print(result)


    







    
    