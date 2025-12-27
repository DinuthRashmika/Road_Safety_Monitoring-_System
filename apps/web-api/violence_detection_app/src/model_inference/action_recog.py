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
        

    def action_recognition_real(self, f_buffer):

        #Check if frame_buffer is full
        if len(self.frame_buffer) < self.sequence_length:
            return {
                'action': 'Waiting...',
                'confidence': 0.0,
                'ready': False,
                'all_probabilities': {}
            }
        
        #Convert buffer to array
        lrcn_sequence = np.array(list(self.frame_buffer))
        #Add Batch Dimensions (1, sequence_length, width, height, 3)
        lrcn_batch = np.expand_dims(lrcn_sequence, axis=0)

        #Run LRCN
        if self.lrcn_model is not None:
            predictions = self.lrcn_model.predict(lrcn_batch, verbose=0)[0]
        else:
            print("From action_recognition_real method. Model not found")
            
        #Get predicted action 
        action_id = np.argmax(predictions)
        confidence = float(predictions[action_id])
        action_name = self.action_classes[action_id]

        #All probabilities
        all_probs = {
            self.actions[i]: float(predictions[i])
            for i in range(len(predictions))
        }

        #Update States
        self.current_action = action_name
        self.action_confidence = confidence

        return {
            'action': action_name,
            'confidence': confidence,
            'ready': True,
            'all_probabilities': all_probs
        }
        

    def classify_video(self, video_path, frame_extractor):
        """
        Complete pipeline: Extract frames → Preprocess → Classify.
        
        Args:
            video_path (str): Path to video file
            frame_extractor (FrameExtractor): FrameExtractor instance
            
        Returns:
            dict: Classification results
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"LRCN VIDEO CLASSIFICATION")
            print(f"Video: {os.path.basename(video_path)}")
            print(f"{'='*70}\n")
        
        # Step 1: Extract frames
        if self.verbose:
            print("[1/3] Extracting frames...")
        frames = frame_extractor.extract_frames(video_path)
        if self.verbose:
            print(f"✓ Extracted {len(frames)} frames\n")
        
        # Step 2: Preprocess for LRCN
        if self.verbose:
            print("[2/3] Preprocessing for LRCN...")
        lrcn_sequence = frame_extractor.preprocess_for_lrcn(frames)
        if self.verbose:
            print(f"✓ Sequence ready: {lrcn_sequence.shape}\n")
        
        # Step 3: Classify
        if self.verbose:
            print("[3/3] Running classification...")
        results = self.action_recognition(lrcn_sequence)
        
        # Print summary
        if self.verbose:
            self._print_results(results, video_path)
        
        return results
    
