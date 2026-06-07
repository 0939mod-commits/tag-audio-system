"""Audio utility functions for processing and analysis"""
import numpy as np
import librosa
from scipy import signal
from scipy.fftpack import fft, ifft
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, filtfilt
import warnings
warnings.filterwarnings('ignore')

from config import *


class AudioProcessor:
    """Main audio processing class"""
    
    @staticmethod
    def load_audio(file_path, sr=SAMPLE_RATE, mono=True):
        """Load audio file with error handling"""
        try:
            y, sr = librosa.load(file_path, sr=sr, mono=mono)
            return y, sr
        except Exception as e:
            raise Exception(f"Error loading audio: {str(e)}")
    
    @staticmethod
    def normalize_audio(y, target_db=-20):
        """Normalize audio to target loudness"""
        S = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE)
        S_db = librosa.power_to_db(S, ref=np.max)
        current_db = np.mean(S_db)
        gain = 10 ** ((target_db - current_db) / 20.0)
        return np.clip(y * gain, -1.0, 1.0)
    
    @staticmethod
    def extract_mfcc(y, sr=SAMPLE_RATE, n_mfcc=13):
        """Extract MFCC features"""
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        return np.mean(mfcc, axis=1)
    
    @staticmethod
    def extract_mfcc_sequence(y, sr=SAMPLE_RATE, n_mfcc=13):
        """Extract MFCC features sequence for time-series matching"""
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        return mfcc.T  # Return transposed for time-series
    
    @staticmethod
    def extract_spectral_features(y, sr=SAMPLE_RATE):
        """Extract spectral features (centroid, rolloff, bandwidth)"""
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        
        return {
            'centroid_mean': np.mean(spectral_centroid),
            'centroid_std': np.std(spectral_centroid),
            'rolloff_mean': np.mean(spectral_rolloff),
            'rolloff_std': np.std(spectral_rolloff),
            'bandwidth_mean': np.mean(spectral_bandwidth),
            'bandwidth_std': np.std(spectral_bandwidth)
        }
    
    @staticmethod
    def compute_stft(y, sr=SAMPLE_RATE):
        """Compute Short-Time Fourier Transform"""
        D = librosa.stft(y, n_fft=FFT_SIZE, hop_length=HOP_LENGTH)
        magnitude = np.abs(D)
        phase = np.angle(D)
        return magnitude, phase
    
    @staticmethod
    def compute_mel_spectrogram(y, sr=SAMPLE_RATE):
        """Compute mel-spectrogram"""
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=FFT_SIZE, 
                                          hop_length=HOP_LENGTH, n_mels=N_MELS)
        S_db = librosa.power_to_db(S, ref=np.max)
        return S_db
    
    @staticmethod
    def compute_mel_spectrogram_normalized(y, sr=SAMPLE_RATE):
        """Compute normalized mel-spectrogram for comparison"""
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=FFT_SIZE, 
                                          hop_length=HOP_LENGTH, n_mels=N_MELS)
        S_db = librosa.power_to_db(S, ref=np.max)
        # Normalize per time frame
        S_normalized = (S_db - np.mean(S_db, axis=0)) / (np.std(S_db, axis=0) + 1e-8)
        return S_normalized
    
    @staticmethod
    def dynamic_time_warping(x, y, window=DTW_WINDOW):
        """Dynamic Time Warping distance with constrained window"""
        n, m = len(x), len(y)
        dtw_matrix = np.full((n + 1, m + 1), np.inf)
        dtw_matrix[0, 0] = 0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if abs(i - j) <= window:
                    if isinstance(x[i-1], np.ndarray) and isinstance(y[j-1], np.ndarray):
                        cost = np.sqrt(np.sum((x[i-1] - y[j-1])**2))
                    else:
                        cost = abs(float(x[i-1]) - float(y[j-1]))
                    dtw_matrix[i, j] = cost + min(dtw_matrix[i-1, j],
                                                   dtw_matrix[i, j-1],
                                                   dtw_matrix[i-1, j-1])
        
        return dtw_matrix[n, m] / (n + m)  # Normalize by path length
    
    @staticmethod
    def compute_correlation(x, y):
        """Compute normalized cross-correlation"""
        x = np.asarray(x)
        y = np.asarray(y)
        x = (x - np.mean(x)) / (np.std(x) + 1e-8)
        y = (y - np.mean(y)) / (np.std(y) + 1e-8)
        correlation = signal.correlate(x, y, mode='valid')
        return np.max(correlation) / len(x)
    
    @staticmethod
    def extract_energy_envelope(y, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
        """Extract energy envelope of the signal"""
        S = librosa.feature.melspectrogram(y=y, sr=sr, hop_length=hop_length)
        S_db = librosa.power_to_db(S, ref=np.max)
        energy = np.mean(S_db, axis=0)
        return energy
    
    @staticmethod
    def detect_silence(y, sr=SAMPLE_RATE, threshold_db=-40):
        """Detect silent regions"""
        S = librosa.feature.melspectrogram(y=y, sr=sr)
        S_db = librosa.power_to_db(S, ref=np.max)
        energy = np.mean(S_db, axis=0)
        silence_frames = energy < threshold_db
        return silence_frames
    
    @staticmethod
    def smooth_signal(y, window_size=SMOOTHING_WINDOW):
        """Smooth signal using Gaussian filter"""
        return gaussian_filter1d(y, sigma=window_size/6)
    
    @staticmethod
    def apply_hann_window(y, window_size):
        """Apply Hann window to signal"""
        window = signal.get_window('hann', window_size)
        return y * window
    
    @staticmethod
    def remove_dc_offset(y):
        """Remove DC offset from audio"""
        return y - np.mean(y)
    
    @staticmethod
    def preprocess_audio(y, sr=SAMPLE_RATE):
        """Complete preprocessing pipeline"""
        y = AudioProcessor.remove_dc_offset(y)
        y = AudioProcessor.normalize_audio(y)
        return y
    
    @staticmethod
    def time_to_samples(time_seconds, sr=SAMPLE_RATE):
        """Convert time in seconds to sample count"""
        return int(time_seconds * sr)
    
    @staticmethod
    def samples_to_time(samples, sr=SAMPLE_RATE):
        """Convert sample count to time in seconds"""
        return samples / sr
    
    @staticmethod
    def apply_high_pass_filter(y, sr=SAMPLE_RATE, cutoff_hz=80):
        """Apply high-pass filter to remove low-frequency noise"""
        nyquist = sr / 2
        normalized_cutoff = cutoff_hz / nyquist
        b, a = butter(4, normalized_cutoff, btype='high')
        return filtfilt(b, a, y)
