import os
from datetime import datetime
import cv2
import sys
import numpy as np
from violence_detection_app.src.config import config

class VideoHandler:

    def __init__(self):
        self.upload_dir = config.RESULTS_DIR

    def check_opencv_status(self):
        """Checks for OpenCV import status and version."""
        if 'cv2' in sys.modules and cv2.__version__:
            print("\n Pamali Again cv2 (OpenCV) module imported successfully.")
            print(f"OpenCV Version: {cv2.__version__}")
        else:
            print("\ncv2 (OpenCV) module FAILED to import.")


    # Reads video using OpenCV
    def read_video(self, video_path):

        print("----Opening Video----")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Unable to open video: {video_path}")
        
        return cap

    # Reads the input video, gives info (FPS, width, height)
    def get_video_properties(self, video_path):

        print("----Capturing Video Properties----")
        cap = self.read_video(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        bitrate = int(cap.get(cv2.CAP_PROP_BITRATE))

        print(f"FPS: {fps}")
        print(f"Total Frames: {frame_count}")
        print(f"Resolution (w x h): {width}x{height}")
        print(f"Duration: {duration}")
        print(f"Bitrate: {bitrate}")

        cap.release()

        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "bitrate": bitrate
        }

    # # Prepares a video file to write frames into u
    # def prepare_video(output_path, fourcc_str, fps, frame_size):

    #     os.makedirs(os.path.dirname(output_path), exist_ok=True)
    #     fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
    #     writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
    #     print("Step 1.2 - Video Opened")
    #     if not writer.isOpened():
    #         raise RuntimeError(f"Step 1.2 Error - Unable to open video writer for: {output_path}")
        
    #     return writer


if __name__ == "__main__":
    handler = VideoHandler()
    handler.check_opencv_status()
    cap = handler.read_video(config.VIDEO_PATH)
    handler.get_video_properties(config.VIDEO_PATH)
    print("----Finished----")

    import psutil

    print(psutil.virtual_memory())


