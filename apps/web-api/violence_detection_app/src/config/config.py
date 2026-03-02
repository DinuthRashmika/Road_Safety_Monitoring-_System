import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
NOTEBOOKS_DIR = os.path.join(PROJECT_ROOT, 'notebooks')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

# Video Settings
ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv']
MAX_VIDEO_SIZE_MB = 500
TARGET_FPS = 10
VIDEO_PATH = os.path.join(DATA_DIR, 'sample', 'shooting_test_front.mp4')
OUTPUT_DIR = os.path.join(RESULTS_DIR, 'yolo_output')
SAVED_FRAMES = os.path.join(DATA_DIR, 'frames')


# YOLO Settings
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, 'yolo', 'best_v2.pt')
YOLO_IMAGE_WIDTH = 640
YOLO_IMAGE_HEIGHT = 640
YOLO_CONFIDENCE_THRESHOLD = 0.25
VIOLENT_OBJECTS = ['person', 'knife', 'gun', 'stick']
OBJECT_WEIGHTS = {
    "knife":0.9, 
    "gun":1.0, 
    "stick":0.5
}
OBJECT_DETECTION_WEIGHT = 0.4

# CNN+LSTM LRCN Settings
LRCN_MODEL_PATH = os.path.join(MODELS_DIR, 'cnn', 'LRCN_model__Date_Time_2025_12_09__14_26_05__Loss_0.28958943486213684__Accuracy_0.9262295365333557.h5')
LRCN_TORCH_MODEL_PATH = os.path.join(MODELS_DIR, 'cnn', 'LRCN_PyTorch__Date_Time_2026_02_26__20_58_31__Loss_1.1831__Accuracy_70.31.pth')
LRCN_IMAGE_HEIGHT = 128 
LRCN_IMAGE_WIDTH = 128
LRCN_CONFIDENCE_THRESHOLD = 0.7
SEQUENCE_LENGTH = 16
VIOLENT_ACTIONS = ["Fighting", "Running", "Attacking", "Shooting"]
ACTION_WEIGHTS = {
    "shooting":1.0, 
    "running":0.7, 
    "attacking":0.9, 
    "fighting":0.8
}
ACTION_RECOGNITION_WEIGHT = 0.6



print(f"Project Root (Read from Config file): {LRCN_MODEL_PATH}")