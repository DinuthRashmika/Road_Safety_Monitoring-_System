import os
import cv2
import numpy as np
from violence_detection_app.src.config import config
from violence_detection_app.src.data_processing.video_handler import VideoHandler

class FrameExtractor:

    def __init__(self, target_fps=None):
        self.handler = VideoHandler()

        self.target_fps = target_fps or config.TARGET_FPS
        self.sequence_length = config.SEQUENCE_LENGTH
        self.yolo_width = config.YOLO_IMAGE_WIDTH
        self.yolo_height = config.YOLO_IMAGE_HEIGHT
        self.lrcn_width = config.LRCN_IMAGE_WIDTH
        self.lrcn_height = config.LRCN_IMAGE_HEIGHT

    def extract_frames(self, video_path):

        cap = self.handler.read_video(video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = max(int(video_fps / self.target_fps), 1)
        print(f"Frame Interval: {frame_interval}")
        print(f"Total number of frames in the video: {cap.get(cv2.CAP_PROP_FRAME_COUNT)}")
        print(f"----Starting Extracting frames at target FPS: {self.target_fps}")
        
        frames = []
        frames_count = 0
        extracted_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frames_count % frame_interval == 0:
                timestamp = frames_count / video_fps
                frames.append(frame)
                extracted_count += 1
            
            frames_count += 1
        
        cap.release()
        print(f"Extracted {extracted_count} frames")

        return frames #50 