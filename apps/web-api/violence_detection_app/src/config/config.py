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
VIDEO_PATH = os.path.join(DATA_DIR, 'sample', 'shooting_test_1.mp4')
OUTPUT_DIR = os.path.join(RESULTS_DIR, 'yolo_output')
SAVED_FRAMES = os.path.join(DATA_DIR, 'frames')

# YOLO Settings
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, 'yolo', 'best_v2.pt')
YOLO_IMAGE_WIDTH = 640
YOLO_IMAGE_HEIGHT = 640
YOLO_CONFIDENCE_THRESHOLD = 0

# CNN+LSTM LRCN Settings
LRCN_MODEL_PATH = os.path.join(MODELS_DIR, 'lrcn', 'LRCN_model__Date_Time_2025_12_09__14_26_05__Loss_0.28958943486213684__Accuracy_0.9262295365333557.h5')
LRCN_IMAGE_HEIGHT = 128 
LRCN_IMAGE_WIDTH = 128
LRCN_CONFIDENCE_THRESHOLD = 0
SEQUENCE_LENGTH = 16

VIOLENT_OBJECTS = ['person', 'knife', 'gun', 'stick']
VIOLENT_ACTIONS = ['running', 'shooting', 'fighting', 'attacking']


print(f"Project Root (Read from Config file): {PROJECT_ROOT}")