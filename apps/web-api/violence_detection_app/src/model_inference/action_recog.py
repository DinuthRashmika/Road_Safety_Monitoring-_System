from collections import deque
import os
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
# import warnings
# warnings.filterwarnings('ignore', category=FutureWarning)
import numpy as np
from tensorflow import keras
import tensorflow
from violence_detection_app.src.config import config
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.src.data_processing.frame_extractor import FrameExtractor

class ActionDetection:

    def __init__(self, model_path=None, confidence_threshold=None, sequence_length=None, verbose=True):
        self.handler = VideoHandler()
        self.frame_extractor = FrameExtractor()

        self.model_path = model_path or config.LRCN_MODEL_PATH
        self.confidence_threshold = confidence_threshold or config.LRCN_CONFIDENCE_THRESHOLD
        self.sequence_length = config.SEQUENCE_LENGTH
        self.verbose = verbose

        self.action_classes = config.VIOLENT_ACTIONS

        print("NumPy:", np.__version__)
        print("TensorFlow:", tensorflow.__version__)
        print("Keras:", keras.__version__)

        # Model load
        self.lrcn_model = self.load_lrcn_model(model_path) 
        # Sliding window buffer
        self.frame_buffer = deque(maxlen=sequence_length)

        self.current_action = "Initializing"
        self.action_confidence = 0.0
        self.detected_weapons = []

        self.stats = {
            'frames_processes': 0,
            'actions_detected': 0,
            'alerts_triggered': 0
        }



    def load_lrcn_model(self, model_path):

        if self.verbose:
            print("----Loading LRCN Model----")
        
        try:
            from tensorflow import keras

            if model_path is None:
                model_path = config.LRCN_MODEL_PATH

            if not os.path.exists(model_path):
                if self.verbose:
                    print(f"Model file not found: {model_path}")
                    print("Using mock model for testing.\n")
                return None

            model = keras.models.load_model(model_path)
            
            if self.verbose:
                print(f"LRCN model loaded successfully!")
                print(f"Model: {model_path}")
                print(f"Input shape: {model.input_shape}")
                print(f"Output shape: {model.output_shape}\n")

            return model
        
        except ImportError:
            if self.verbose:
                print("TensorFlow/Keras not installed. Using default model.")
                print("Install with: pip install tensorflow\n")
            return None
        
        except Exception as e:
            if self.verbose:
                print(f"Error loading LRCN: {e}")
                print("Using default model for testing.\n")
            return None
        
