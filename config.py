"""Configuration file for Audio Tag Detection System"""
import os
from pathlib import Path

# Supported input formats
SUPPORTED_FORMATS = ['.mkv', '.aac', '.wav', '.mp3', '.mp4']

# Output configuration
OUTPUT_BITRATE = '128k'
OUTPUT_FORMAT = 'aac'
OUTPUT_CODEC = 'aac'

# Audio processing parameters
SAMPLE_RATE = 44100
FFT_SIZE = 2048
HOP_LENGTH = 512
N_MELS = 128

# Tag detection parameters
MIN_TAG_DURATION = 0.3  # Minimum duration of tag in seconds
MAX_TAG_DURATION = 8.0  # Maximum duration of tag in seconds
CORRELATION_THRESHOLD = 0.80  # High correlation threshold for precision
DTW_THRESHOLD = 0.75  # DTW similarity threshold
NOISE_THRESHOLD = 0.05  # Threshold for background noise
DTW_WINDOW = 100  # Dynamic Time Warping window size
MULTIPLE_DETECTION_THRESHOLD = 0.5  # Allow multiple detections with gap

# Processing parameters
CHUNK_SIZE = 4096
OVERLAP_RATIO = 0.5
SMOOTHING_WINDOW = 21
MIN_GAP_BETWEEN_TAGS = 0.2  # Minimum gap between tags in seconds

# Paths
TEMP_DIR = Path('./temp_processing')
OUTPUT_DIR = Path('./output')
LOG_DIR = Path('./logs')

# Create directories if they don't exist
for directory in [TEMP_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Detection algorithm parameters
USE_SPECTRAL_ANALYSIS = True
USE_MFCC_ANALYSIS = True
USE_DTW_MATCHING = True
USE_ENVELOPE_MATCHING = True
ENSEMBLE_METHOD = 'voting'  # 'voting' or 'averaging'
