import cv2
import time
import threading
from datetime import datetime
from typing import Optional, Callable
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CameraHandler:
    def __init__(self, source: int = 0, fps: int = 30, frame_skip: int = 5):
        self.source = source
        self.fps = fps
        self.frame_skip = frame_skip
        self.cap = None
        self.is_running = False
        self.frame_count = 0
        self.current_frame = None
        self.callback = None
        
    def start(self, callback: Optional[Callable] = None):
        """Start camera capture"""
        self.callback = callback
        self.cap = cv2.VideoCapture(self.source)
        
        if not self.cap.isOpened():
            logger.error(f"Cannot open camera source {self.source}")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera started on source {self.source}")
        return True
    
    def _capture_loop(self):
        """Main capture loop"""
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                logger.error("Failed to grab frame")
                time.sleep(1)
                continue
            
            self.current_frame = frame
            self.frame_count += 1
            
            # Process every nth frame
            if self.frame_count % self.frame_skip == 0 and self.callback:
                try:
                    self.callback(frame.copy(), self.frame_count)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            # Maintain FPS
            time.sleep(1 / self.fps)
    
    def get_frame(self):
        """Get current frame"""
        return self.current_frame
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        logger.info("Camera stopped")
    
    def save_frame(self, frame, directory: str = "detections"):
        """Save frame to disk"""
        Path(directory).mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{directory}/detection_{timestamp}.jpg"
        
        cv2.imwrite(filename, frame)
        logger.info(f"Frame saved: {filename}")
        return filename