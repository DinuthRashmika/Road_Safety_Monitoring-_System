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
                timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                timestamp_sec = round(timestamp_ms / 1000.0, 3)
                frames.append({
                    "timestamp": timestamp_ms,
                    "frame": frame
                    })
                extracted_count += 1
            
            frames_count += 1
        
        cap.release()
        print(f"Extracted {extracted_count} frames")

        return frames #50 


    def extract_each_frame(self, video_source):

        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            print(f"Error: Cannot open video source: {video_source}")
            return
        
        frame_index = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("📹 End of video stream")
                break
            
            yield frame_index, frame #tuple - (frame_index, frame)
            frame_index += 1
        
        cap.release()   

    # Preprocess extracted frames for YOLO
    def preprocess_frame_for_yolo(self, frames):
        
        yolo_frames = []
        print(f"----Preparing frames for YOLO----")
        for frame in frames:

            # 1. Resize to YOLO input size (640x640)
            resized = cv2.resize(frame, (self.yolo_width, self.yolo_height))
            # 2. Convert BGR to RGB
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            # 3. Normalize
            normalized = rgb_frame.astype("float32") / 255.0
            # 4. Transpose to (channels, height, width) if needed
            # 5. Add batch dimension if needed

            yolo_frames.append(normalized)

        print(f"Ready for YOLO model input!\n") 
        return yolo_frames
    

    def preprocess_frame_for_lrcn(self, frame):

        resized = cv2.resize(frame, (self.lrcn_width, self.lrcn_height))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = rgb.astype('float32') / 255.0

        print(f"Output Shape: {normalized}")

        return normalized
    

    # Preprocess extracted frames for LRCN
    def preprocess_for_lrcn(self, frames):

        num_frames = len(frames)
        print(f"----Preparing LRCN sequence for LRCN----")

        if num_frames >= self.sequence_length:
            indices = np.linspace(0, num_frames - 1, self.sequence_length, dtype=int)
            sampled_frames = [frames[i] for i in indices]
            print(f"Sampled Indices: {indices.tolist()}")
        else:
            print(f"Warning! Video is too short. Padding {self.sequence_length - num_frames} frames")
            sampled_frames = frames + [frames[-1]] * (self.sequence_length - num_frames)
            if len(sampled_frames) == self.sequence_length:
                print("Final length = SEQUENCE_LENGTH from padding also!")

        normalized_frames = []
        for frame in sampled_frames:
            resized = cv2.resize(frame, (self.lrcn_width, self.lrcn_height))
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            normalized = rgb_frame.astype('float') / 255.0
            normalized_frames.append(normalized)

        array_sequence = np.array(normalized_frames)
        print(f"LRCN array sequence shape: {array_sequence.shape}")

        lrcn_sequence = np.expand_dims(array_sequence, axis=0)
        print(f"LRCN sequence shape: {lrcn_sequence.shape}")
        print(f"Ready for LRCN model input!\n")
        
        return lrcn_sequence

    # def 

    # Save Frames
    def save_frames(self, frames, video_path, model_name, output_folder):

        video = os.path.basename(video_path)
        video_name = os.path.splitext(video)[0]
        frame_folder = os.path.join(output_folder, video_name, model_name)
        os.makedirs(frame_folder, exist_ok=True)

        for i, item in enumerate(frames):

            frame = item["frame"]
            timestamp = item["timestamp"]

            # Convert back to 255 to view
            new_frame = (frame * 255).astype(np.uint8)
            # RGB -> BGR to view
            new_frame = cv2.cvtColor(new_frame, cv2.COLOR_RGB2BGR)

            filename = f"frame_{model_name}_{i:04d}_ts_{timestamp:.3f}.jpg"
            filepath = os.path.join(frame_folder, filename)
            
            cv2.imwrite(filepath, new_frame)

        print(f"Saved {len(frames)} Frames to {frame_folder}")


if __name__ == "__main__":
    frame_extract = FrameExtractor()
    
    frames = frame_extract.extract_frames(config.VIDEO_PATH)
    # lrcn_seq = frame_extract.preprocess_for_lrcn(frames)
    frame_extract.save_frames(frames, config.VIDEO_PATH, 'lrcn', config.SAVED_FRAMES)