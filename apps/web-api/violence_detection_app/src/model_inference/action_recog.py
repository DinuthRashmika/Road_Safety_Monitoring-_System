from collections import deque
import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from violence_detection_app.src.config import config
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.src.data_processing.frame_extractor import FrameExtractor


# ============================================
# LRCN MODEL DEFINITION (MUST MATCH TRAINING)
# ============================================
class LRCNModel(nn.Module):
    """
    PyTorch LRCN Model for Action Recognition
    MUST match your training model exactly!
    """
    
    def __init__(self, num_classes=4, lstm_hidden=32):
        super(LRCNModel, self).__init__()
        
        # CNN Feature Extractor
        self.cnn = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(4),
            nn.Dropout(0.25),
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(4),
            nn.Dropout(0.25),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.25),
            
            # CRITICAL: NO DROPOUT in last conv block (matching TensorFlow)
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        
        self.cnn_output_size = 64 * 2 * 2  # 256
        
        # LSTM
        self.lstm = nn.LSTM(
            input_size=self.cnn_output_size,
            hidden_size=lstm_hidden,
            num_layers=1,
            batch_first=True
        )
        
        # Classifier
        self.fc = nn.Linear(lstm_hidden, num_classes)
    
    def forward(self, x):
        """Forward pass"""
        batch_size, seq_len, C, H, W = x.size()
        
        # Process frames through CNN
        x = x.view(batch_size * seq_len, C, H, W)
        x = self.cnn(x)
        
        # Reshape for LSTM
        x = x.contiguous().view(batch_size * seq_len, -1)
        x = x.contiguous().view(batch_size, seq_len, -1)
        
        # LSTM
        lstm_out, _ = self.lstm(x)
        x = lstm_out[:, -1, :]
        
        # Classification
        return self.fc(x)


# ============================================
# ACTION RECOGNITION CLASS (PyTorch Version)
# ============================================
class ActionRecognitionTorch:
    def __init__(self, 
                 model_path: str = None,
                 confidence_threshold: float = None,
                 sequence_length: int = None,
                 verbose: bool = True):

        self.verbose = verbose
        
        # Handlers
        self.video_handler = VideoHandler()
        self.frame_extractor = FrameExtractor()
        
        # Configuration
        self.model_path = model_path or config.LRCN_TORCH_MODEL_PATH
        self.confidence_threshold = confidence_threshold or config.LRCN_CONFIDENCE_THRESHOLD
        self.sequence_length = sequence_length or config.SEQUENCE_LENGTH
        
        if self.verbose:
            print(f"Confidence threshold: {self.confidence_threshold}")
        
        # Action classes
        self.action_classes = config.VIOLENT_ACTIONS
        self.num_classes = len(self.action_classes)
        
        # Device (GPU if available)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if self.verbose:
            print(f"Using device: {self.device}")
        
        # Load PyTorch LRCN model
        self.lrcn_model = self._load_lrcn_model(self.model_path)
        
        # Sliding window buffer
        self.frame_buffer = deque(maxlen=self.sequence_length)
        
        # Current state
        self.current_action = "Initializing"
        self.action_confidence = 0.0
        
        # Statistics
        self.stats = {
            'frames_processed': 0,
            'sequences_analyzed': 0,
            'violent_actions_detected': 0,
            'action_distribution': {action: 0 for action in self.action_classes}
        }
        
        if self.verbose:
            print(f"\n{'='*70}")
            print("PYTORCH LRCN ACTION DETECTOR INITIALIZED")
            print(f"{'='*70}")
            print(f"Model: {os.path.basename(self.model_path)}")
            print(f"Device: {self.device}")
            print(f"Sequence Length: {self.sequence_length} frames")
            print(f"Confidence Threshold: {self.confidence_threshold}")
            print(f"Action Classes: {', '.join(self.action_classes)}")
            print(f"{'='*70}\n")
    
    
    def _load_lrcn_model(self, model_path: str):
        """
        Load trained PyTorch LRCN model
        
        Args:
            model_path: Path to .pth model file
        
        Returns:
            Loaded PyTorch model or None
        """
        if self.verbose:
            print("Loading PyTorch LRCN model...")
        
        try:
            if not os.path.exists(model_path):
                print(f" Model file not found: {model_path}")
                print("   Using mock model for testing\n")
                return None
            
            # Create model
            model = LRCNModel(num_classes=self.num_classes, lstm_hidden=32).to(self.device)
            
            # Load weights
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            
            # Set to evaluation mode
            model.eval()
            
            if self.verbose:
                print(f"PyTorch LRCN model loaded successfully!")
                total_params = sum(p.numel() for p in model.parameters())
                print(f"   Total parameters: {total_params:,}")
                print(f"   Model architecture: CNN + LSTM\n")
            
            return model
        
        except Exception as e:
            print(f" Error loading PyTorch LRCN model: {e}\n")
            import traceback
            traceback.print_exc()
            return None
    
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess single frame for PyTorch LRCN
        
        Args:
            frame: Raw frame from video (H, W, 3) in BGR
        
        Returns:
            Preprocessed frame (128, 128, 3) in RGB, normalized
        """
        # CRITICAL: Use same size as training (128x128, NOT 64x64!)
        resized = cv2.resize(frame, (128, 128))
        
        # Convert BGR to RGB (OpenCV uses BGR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        normalized = rgb / 255.0
        
        return normalized
    
    
    def add_frame_to_buffer(self, frame: np.ndarray) -> bool:
        """
        Add preprocessed frame to sliding window buffer
        
        Args:
            frame: Raw frame from video
        
        Returns:
            True if buffer is full and ready for prediction
        """
        # Preprocess frame
        preprocessed = self.preprocess_frame(frame)
        
        # Add to buffer
        self.frame_buffer.append(preprocessed)
        
        # Check if buffer is full
        return len(self.frame_buffer) == self.sequence_length
    
    
    def predict_action(self) -> Dict:
        """
        Predict action from current frame buffer using PyTorch
        
        Returns:
            Dictionary with prediction results
        """
        # Check if buffer is full
        if len(self.frame_buffer) < self.sequence_length:
            return {
                'action': 'Waiting...',
                'confidence': 0.0,
                'ready': False,
                'all_probabilities': {},
                'is_violent': False
            }
        
        # Check if model is loaded
        if self.lrcn_model is None:
            return {
                'action': 'Model not loaded',
                'confidence': 0.0,
                'ready': False,
                'all_probabilities': {},
                'is_violent': False
            }
        
        # Convert buffer to numpy array
        # Shape: (sequence_length, 128, 128, 3)
        lrcn_sequence = np.array(list(self.frame_buffer))
        
        # Convert to PyTorch tensor
        # Shape: (1, sequence_length, 128, 128, 3)
        lrcn_tensor = torch.FloatTensor(lrcn_sequence).unsqueeze(0)
        
        # Permute to PyTorch format: (1, sequence_length, 3, 128, 128)
        lrcn_tensor = lrcn_tensor.permute(0, 1, 4, 2, 3)
        
        # Move to device
        lrcn_tensor = lrcn_tensor.to(self.device)
        
        # Run prediction
        with torch.no_grad():
            outputs = self.lrcn_model(lrcn_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            probabilities = probabilities.cpu().numpy()
        
        # Get predicted action
        action_id = np.argmax(probabilities)
        confidence = float(probabilities[action_id])
        action_name = self.action_classes[action_id]
        
        # All action probabilities
        all_probabilities = {
            self.action_classes[i]: float(probabilities[i])
            for i in range(len(probabilities))
        }
        
        # Update current state
        self.current_action = action_name
        self.action_confidence = confidence
        
        # Update statistics
        self.stats['sequences_analyzed'] += 1
        self.stats['action_distribution'][action_name] += 1
        
        # Check if violent
        is_violent = action_name in config.VIOLENT_ACTIONS and confidence > self.confidence_threshold
        if is_violent:
            self.stats['violent_actions_detected'] += 1
        
        return {
            'action': action_name,
            'confidence': confidence,
            'ready': True,
            'all_probabilities': all_probabilities,
            'is_violent': is_violent
        }
    
    
    def process_single_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame (main API method)
        
        Args:
            frame: Raw frame from video/stream
        
        Returns:
            LRCN prediction results
        """
        self.stats['frames_processed'] += 1
        
        # Add frame to buffer
        buffer_ready = self.add_frame_to_buffer(frame)
        
        # If buffer is full, make prediction
        if buffer_ready:
            return self.predict_action()
        else:
            return {
                'action': 'Buffering...',
                'confidence': 0.0,
                'ready': False,
                'all_probabilities': {},
                'is_violent': False,
                'buffer_progress': len(self.frame_buffer),
                'buffer_size': self.sequence_length
            }
    
    
    def reset_buffer(self):
        """Reset the frame buffer"""
        self.frame_buffer.clear()
        if self.verbose:
            print("Frame buffer reset")
    
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        stats = self.stats.copy()
        
        # Add percentages
        if stats['sequences_analyzed'] > 0:
            stats['violence_rate'] = (
                stats['violent_actions_detected'] / stats['sequences_analyzed'] * 100
            )
        else:
            stats['violence_rate'] = 0.0
        
        return stats
    
    
    def print_statistics(self):
        """Print formatted statistics"""
        print(f"\n{'='*70}")
        print("LRCN ACTION DETECTION STATISTICS")
        print(f"{'='*70}")
        print(f"Frames Processed: {self.stats['frames_processed']}")
        print(f"Sequences Analyzed: {self.stats['sequences_analyzed']}")
        print(f"Violent Actions Detected: {self.stats['violent_actions_detected']}")
        
        if self.stats['sequences_analyzed'] > 0:
            violence_rate = self.stats['violent_actions_detected'] / self.stats['sequences_analyzed'] * 100
            print(f"Violence Rate: {violence_rate:.2f}%")
        
        print(f"\nAction Distribution:")
        for action, count in self.stats['action_distribution'].items():
            if self.stats['sequences_analyzed'] > 0:
                percentage = count / self.stats['sequences_analyzed'] * 100
                print(f"  {action.capitalize():12s}: {count:4d} ({percentage:5.1f}%)")
            else:
                print(f"  {action.capitalize():12s}: {count:4d}")
        
        print(f"{'='*70}\n")
    
    
    def process_video_file_test(self, video_path: str, display: bool = True, save_output: str = None) -> Dict:
        """
        Process entire video file (for testing)
        
        Args:
            video_path: Path to video file
            display: Show annotated video
            save_output: Path to save output (optional)
        
        Returns:
            Final statistics
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"PROCESSING VIDEO FILE (PyTorch)")
            print(f"{'='*70}")
            print(f"Video: {os.path.basename(video_path)}")
            print(f"Press 'q' to quit")
            print(f"{'='*70}\n")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f" Error: Cannot open video: {video_path}")
            return {}
        
        # Get properties
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video Properties:")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps}")
        print(f"  Total Frames: {total_frames}")
        print(f"  Duration: {total_frames/fps:.1f} seconds\n")
        
        # Video writer (optional)
        video_writer = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_output, fourcc, fps, (width, height))
            print(f"Saving output to: {save_output}\n")
        
        # Reset statistics
        self.reset_buffer()
        self.stats = {
            'frames_processed': 0,
            'sequences_analyzed': 0,
            'violent_actions_detected': 0,
            'action_distribution': {action: 0 for action in self.action_classes}
        }
        
        current_result = None
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("\nEnd of video")
                    break
                
                # Process frame
                result = self.process_single_frame(frame)
                
                # Update current result if prediction was made
                if result['ready']:
                    current_result = result
                    
                    if self.verbose and self.stats['frames_processed'] % 30 == 0:
                        print(f"Frame {self.stats['frames_processed']}/{total_frames}: "
                              f"{result['action'].upper()} "
                              f"({result['confidence']*100:.1f}%)")
                
                # Annotate frame
                annotated = self._draw_lrcn_only_annotations_test(
                    frame,
                    result,
                    self.stats['frames_processed']
                )
                
                # Display
                if display:
                    cv2.imshow('PyTorch LRCN Action Detection', annotated)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nStopped by user")
                        break
                
                # Save
                if video_writer:
                    video_writer.write(annotated)
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            cap.release()
            if video_writer:
                video_writer.release()
            if display:
                cv2.destroyAllWindows()
            
            # Print final statistics
            self.print_statistics()
        
        return self.get_statistics()
    
    
    def _draw_lrcn_only_annotations_test(self, frame: np.ndarray, result: Dict, frame_count: int) -> np.ndarray:
        """
        Draw LRCN-only annotations
        
        Args:
            frame: Original frame
            result: LRCN prediction result
            frame_count: Current frame number
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        height, width = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (width, 250), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)
        
        # Frame count
        cv2.putText(annotated, f"Frame: {frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # PyTorch indicator
        cv2.putText(annotated, "PyTorch", (width - 150, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Buffer status or prediction
        if not result['ready']:
            buffer_progress = result.get('buffer_progress', len(self.frame_buffer))
            buffer_text = f"Buffering: {buffer_progress}/{self.sequence_length}"
            cv2.putText(annotated, buffer_text, (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        else:
            action = result['action']
            confidence = result['confidence']
            
            # Color based on action
            if action in ['shooting', 'fighting', 'attacking']:
                color = (0, 0, 255)  # Red
            elif action == 'running':
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 255, 0)  # Green
            
            # Action name
            cv2.putText(annotated, f"Action: {action.upper()}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            
            # Confidence
            cv2.putText(annotated, f"Confidence: {confidence*100:.1f}%", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Confidence bar
            bar_width = int((width - 40) * confidence)
            cv2.rectangle(annotated, (10, 130), (10 + bar_width, 150), color, -1)
            cv2.rectangle(annotated, (10, 130), (width - 30, 150), (255, 255, 255), 2)
            
            # All probabilities
            y_offset = 180
            cv2.putText(annotated, "All Actions:", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_offset += 25
            
            for action_name, prob in result['all_probabilities'].items():
                text = f"{action_name}: {prob*100:.1f}%"
                cv2.putText(annotated, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                y_offset += 20
            
            # Warning if violent
            if result['is_violent']:
                cv2.putText(annotated, "⚠ VIOLENT ACTION", (width - 350, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        
        return annotated


# ============================================
# MAIN
# ============================================
def main():

    print
    
    # Create detector
    detector = ActionRecognitionTorch(
        model_path=config.LRCN_TORCH_MODEL_PATH,
        confidence_threshold=config.LRCN_CONFIDENCE_THRESHOLD,
        sequence_length=config.SEQUENCE_LENGTH,
        verbose=True
    )
    
    # Test on video file
    detector.process_video_file_test(
        video_path=config.VIDEO_PATH,
        display=True,
        save_output='lrcn_pytorch_output.mp4'
    )


if __name__ == "__main__":
    main()