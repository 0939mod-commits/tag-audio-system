"""Tag removal and replacement module with spectral subtraction"""
import numpy as np
from scipy.signal import istft
import librosa
from scipy.ndimage import gaussian_filter1d
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from config import *
from audio_utils import AudioProcessor


class TagRemover:
    """Remove audio tags while preserving main audio quality"""
    
    @staticmethod
    def remove_tag(video_audio, start_sample, end_sample, sr=SAMPLE_RATE):
        """
        Remove tag using spectral subtraction
        
        Args:
            video_audio: numpy array of video audio
            start_sample: start sample of tag
            end_sample: end sample of tag
            sr: sample rate
            
        Returns:
            audio with tag removed
        """
        output = video_audio.copy()
        tag_length = end_sample - start_sample
        
        # Compute STFT
        D = librosa.stft(output, n_fft=FFT_SIZE, hop_length=HOP_LENGTH)
        magnitude = np.abs(D)
        phase = np.angle(D)
        
        # Convert samples to frames
        start_frame = int(start_sample / HOP_LENGTH)
        end_frame = int(end_sample / HOP_LENGTH)
        
        # Extract tag region
        tag_magnitude = magnitude[:, start_frame:end_frame]
        
        # Compute noise profile from tag region
        noise_profile = np.median(tag_magnitude, axis=1, keepdims=True)
        
        # Spectral subtraction with smoothing
        subtraction_factor = 1.5
        magnitude_cleaned = magnitude.copy()
        magnitude_cleaned[:, start_frame:end_frame] = np.maximum(
            magnitude[:, start_frame:end_frame] - subtraction_factor * noise_profile,
            0.1 * magnitude[:, start_frame:end_frame]
        )
        
        # Apply smoothing at boundaries
        boundary_frames = int(0.05 * sr / HOP_LENGTH)  # 50ms
        boundary_start = max(0, start_frame - boundary_frames)
        boundary_end = min(magnitude.shape[1], end_frame + boundary_frames)
        
        # Smooth transition
        for i in range(boundary_start, start_frame):
            alpha = (i - boundary_start) / (start_frame - boundary_start)
            magnitude_cleaned[:, i] = alpha * magnitude[:, i] + (1 - alpha) * magnitude_cleaned[:, i]
        
        for i in range(end_frame, boundary_end):
            alpha = (i - end_frame) / (boundary_end - end_frame)
            magnitude_cleaned[:, i] = (1 - alpha) * magnitude[:, i] + alpha * magnitude_cleaned[:, i]
        
        # Reconstruct
        D_cleaned = magnitude_cleaned * np.exp(1j * phase)
        output = librosa.istft(D_cleaned, hop_length=HOP_LENGTH, length=len(output))
        
        return output
    
    @staticmethod
    def remove_multiple_tags(video_audio, detections, sr=SAMPLE_RATE):
        """
        Remove multiple tags from audio
        
        Args:
            video_audio: numpy array of video audio
            detections: list of (start_time, end_time, confidence) tuples
            sr: sample rate
            
        Returns:
            audio with all tags removed
        """
        output = video_audio.copy()
        
        print("Removing tags from audio...")
        for start_time, end_time, confidence in tqdm(detections):
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            output = TagRemover.remove_tag(output, start_sample, end_sample, sr)
        
        return output
    
    @staticmethod
    def add_tag_at_position(video_audio, tag_audio, position_time, sr=SAMPLE_RATE):
        """
        Add a tag at specific position
        
        Args:
            video_audio: numpy array of video audio (with tags removed)
            tag_audio: numpy array of tag audio to add
            position_time: position in seconds
            sr: sample rate
            
        Returns:
            audio with new tag added
        """
        output = video_audio.copy()
        position_sample = int(position_time * sr)
        tag_length = len(tag_audio)
        
        # Ensure we don't exceed audio length
        if position_sample + tag_length > len(output):
            tag_audio = tag_audio[:len(output) - position_sample]
        
        # Normalize tag to match surrounding audio
        tag_rms = np.sqrt(np.mean(tag_audio ** 2))
        surrounding_rms = np.sqrt(np.mean(output[max(0, position_sample-sr):position_sample] ** 2))
        
        if surrounding_rms > 0:
            gain = surrounding_rms / (tag_rms + 1e-8)
            tag_audio = tag_audio * gain
        
        # Apply fade in/out to tag
        fade_samples = int(0.01 * sr)  # 10ms fade
        if len(tag_audio) > 2 * fade_samples:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            tag_audio[:fade_samples] *= fade_in
            tag_audio[-fade_samples:] *= fade_out
        
        # Mix tag with background
        tag_mix_level = 0.8  # Keep tag at 80% amplitude for blending
        output[position_sample:position_sample + len(tag_audio)] = (
            (1 - tag_mix_level) * output[position_sample:position_sample + len(tag_audio)] +
            tag_mix_level * tag_audio
        )
        
        return output
    
    @staticmethod
    def add_multiple_tags(video_audio, tag_audio, positions, sr=SAMPLE_RATE):
        """
        Add multiple tags at specified positions
        
        Args:
            video_audio: numpy array of video audio
            tag_audio: numpy array of tag audio
            positions: list of positions in seconds
            sr: sample rate
            
        Returns:
            audio with tags added
        """
        output = video_audio.copy()
        
        print("Adding new tags...")
        for pos in tqdm(positions):
            output = TagRemover.add_tag_at_position(output, tag_audio, pos, sr)
        
        return output
