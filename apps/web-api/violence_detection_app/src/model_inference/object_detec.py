import sys
import traceback
from typing import Dict, List
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

        self.handler = VideoHandler()
        self.frame_extractor = FrameExtractor()

        self.violent_objects = config.VIOLENT_OBJECTS

        self.colors = {
            'knife': (0, 0, 255),      # Red
            'gun': (0, 165, 255),      # Orange
            'stick': (0, 255, 255)     # Yellow
        }

        self.yolo_model = self.load_yolo_model(model_path)

        print(f"Model Path from Parameters: {model_path}")
        print(f"Model Path from self.model_path: {self.model_path}")


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
        
 