from collections import defaultdict
from typing import List


class ModelStatistics:

    def __init__(self):

        self.lrcn_stats = {
            'detection_by_action': defaultdict(int), #{ 'knife': 3, 'gun': 6 }
            'lrcn_confidences': [],
            'min_confidence': None,
            'max_confidence': None,
            'avg_confidence': 0.0
        }

        self.yolo_stats = {
            'detection_by_object': defaultdict(int),
            'yolo_confidences': [],
            'min_confidence': None,
            'max_confidence': None,
            'avg_confidence': 0.0
        }
        
        self.combined_stats = {
            'weighted_scores': [],
            'high_risk_frames': 0, #60t wadi
            'medium_risk_frames': 0, #40t wadi
            'low_risk_frames': 0, #20/30t wadi

        }

        self.total_frames = 0

    def update_lrcn_stats(self, lrcn_result: dict, ready: bool = True):
        
        if not ready:
            return
        
        self.total_frames += 1

        if lrcn_result.get('ready') and lrcn_result.get('is_violent'):
            action = lrcn_result['action']
            confidence = lrcn_result['confidence']

            total_confidence = 0.0

            # 1. detections by action
            # tries to get the current count for this action. If the not in the dictionary returns 0.Adds 1 to the current count
            self.lrcn_stats['detection_by_action'][action] = self.lrcn_stats['detection_by_action'].get(action, 0) + 1 

            # 2. all confidences
            self.lrcn_stats['lrcn_confidences'].append(confidence)

            # 3. min/max confidence
            if self.lrcn_stats.get('min_confidence') is None:
                self.lrcn_stats['min_confidence'] = confidence
                self.lrcn_stats['max_confidence'] = confidence
            else:
                self.lrcn_stats['min_confidence'] = min(self.lrcn_stats['min_confidence'], confidence)
                self.lrcn_stats['max_confidence'] = max(self.lrcn_stats['max_confidence'], confidence)

            # 4. to cal avg
            lrcn_confs = self.lrcn_stats['lrcn_confidences']
            self.lrcn_stats['avg_confidence'] = sum(lrcn_confs) / len(lrcn_confs)


    def update_yolo_stats(self, yolo_result:dict):

        detections = yolo_result.get('detections')

        if not yolo_result:
            return
        
        for det in detections:
            obj_name = det['object']
            confidence = det['confidence']

            # 1. detections by object
            self.yolo_stats['detection_by_object'][obj_name] += 1

            # 2. all confidences
            self.yolo_stats['yolo_confidences'].append(confidence)

            # 3. min/max confidence
            if self.yolo_stats['min_confidence'] is None:
                self.yolo_stats['min_confidence']  = confidence
                self.yolo_stats['max_confidence'] = confidence
            else:
                self.yolo_stats['min_confidence'] = min(self.yolo_stats['min_confidence'], confidence)
                self.yolo_stats['max_confidence'] = max(self.yolo_stats['max_confidence'], confidence)

        # 4. avg confidence
        yolo_confs = self.yolo_stats['yolo_confidences']
        self.yolo_stats['avg_confidence'] = sum(yolo_confs) / len(yolo_confs)


    def update_stats(self, yolo_result=None, lrcn_result=None):

        if yolo_result.get('detections'):
            self.update_yolo_stats(yolo_result)

        if lrcn_result.get('ready') and lrcn_result.get('is_violent'):
            self.update_lrcn_stats(lrcn_result)

    def combine_weights(self, violence_score: float):

        # Store the score
        self.combined_stats['weighted_scores'].append(violence_score)
        
        # Categorize risk level
        if violence_score >= 60:
            self.combined_stats['high_risk_frames'] += 1
        elif violence_score >= 30:
            self.combined_stats['medium_risk_frames'] += 1
        else:
            self.combined_stats['low_risk_frames'] += 1

                

# if __name__ == "__main__":
#     stats = ModelStatistics()

#     lrcn_results = [
#         # Buffering frame (should NOT be counted)
#         {
#             'action': 'Waiting...',
#             'confidence': 0.0,
#             'ready': False,
#             'all_probabilities': {},
#             'is_violent': False
#         },

#         # Violent: fighting
#         {
#             'action': 'fighting',
#             'confidence': 0.82,
#             'ready': True,
#             'all_probabilities': {},
#             'is_violent': True
#         },

#         # Violent: fighting again
#         {
#             'action': 'fighting',
#             'confidence': 0.90,
#             'ready': True,
#             'all_probabilities': {},
#             'is_violent': True
#         },

#         # Violent: attacking
#         {
#             'action': 'attacking',
#             'confidence': 0.75,
#             'ready': True,
#             'all_probabilities': {},
#             'is_violent': True
#         },

#         # Non-violent (should NOT be counted)
#         {
#             'action': 'running',
#             'confidence': 0.65,
#             'ready': True,
#             'all_probabilities': {},
#             'is_violent': False
#         }
#     ]

#     yolo_results = [
#         # Frame 1
#         {
#             'detections': [
#                 {'object': 'knife', 'confidence': 0.72, 'bbox': [10,10,50,50], 'class_id': 43},
#                 {'object': 'person', 'confidence': 0.95, 'bbox': [0,0,100,200], 'class_id': 0}
#             ]
#         },

#         # Frame 2
#         {
#             'detections': [
#                 {'object': 'stick', 'confidence': 0.60, 'bbox': [30,30,80,80], 'class_id': 44}
#             ]
#         },

#         # Frame 3
#         {
#             'detections': [
#                 {'object': 'knife', 'confidence': 0.88, 'bbox': [15,15,60,60], 'class_id': 43},
#                 {'object': 'gun', 'confidence': 0.91, 'bbox': [20,20,70,70], 'class_id': 45}
#             ]
#         }
#     ]

#     #  1//
#     for lrcn_result in lrcn_results:
#         stats.update_lrcn_stats(lrcn_result)

#     for yolo_result in yolo_results:
#         stats.update_yolo_stats(yolo_result)

#     print("----lrcn stats----")
#     print(stats.lrcn_stats)
#     print("----yolo stats----")
#     print(stats.yolo_stats)
#     print(f"confidences: {stats.yolo_stats['yolo_confidences']}" )

    # 2//
    # for frame_idx, (lrcn_result, yolo_result) in enumerate(zip(lrcn_results, yolo_results)):
    #     print(f"processing frame {frame_idx}")
    #     stats.update_stats(yolo_result, lrcn_result)
    
    # print("----lrcn stats----")
    # print(stats.lrcn_stats)
    # print("----yolo stats----")
    # print(stats.yolo_stats)


