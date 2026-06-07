"""Tag detection module with advanced matching algorithms"""
import numpy as np
from scipy import signal
from scipy.spatial.distance import euclidean
import librosa
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from config import *
from audio_utils import AudioProcessor


class TagDetector:
    """Advanced tag detection with ensemble methods"""
    
    def __init__(self, tag_audio, tag_duration, sr=SAMPLE_RATE):
        """
        Initialize detector with reference tag
        
        Args:
            tag_audio: numpy array of tag audio
            tag_duration: duration of tag in seconds
            sr: sample rate
        """
        self.sr = sr
        self.tag_audio = AudioProcessor.preprocess_audio(tag_audio, sr)
        self.tag_duration = tag_duration
        self.tag_samples = int(tag_duration * sr)
        
        # Extract features from tag
        self._extract_tag_features()
    
    def _extract_tag_features(self):
        """Extract and store tag features"""
        # MFCC features
        self.tag_mfcc = AudioProcessor.extract_mfcc_sequence(self.tag_audio, self.sr)
        
        # Mel-spectrogram
        self.tag_mel = AudioProcessor.compute_mel_spectrogram_normalized(self.tag_audio, self.sr)
        
        # Energy envelope
        self.tag_envelope = AudioProcessor.extract_energy_envelope(self.tag_audio, self.sr)
        
        # Spectral features
        self.tag_spectral = AudioProcessor.extract_spectral_features(self.tag_audio, self.sr)
        
        # Chroma features
        self.tag_chroma = librosa.feature.chroma_stft(y=self.tag_audio, sr=self.sr)
    
    def detect_tags(self, video_audio, allow_multiple=False):
        """
        Detect tag locations in video audio
        
        Args:
            video_audio: numpy array of video audio
            allow_multiple: allow multiple detections of same tag
            
        Returns:
            list of (start_time, end_time, confidence) tuples
        """
        video_audio = AudioProcessor.preprocess_audio(video_audio, self.sr)
        video_duration = len(video_audio) / self.sr
        
        # Sliding window detection
        hop_samples = int(0.1 * self.sr)  # 100ms hop
        scores = []
        positions = []
        
        print("Scanning for tags...")
        for start in tqdm(range(0, len(video_audio) - self.tag_samples, hop_samples)):
            end = start + self.tag_samples
            segment = video_audio[start:end]
            
            # Compute similarity score using ensemble
            score = self._compute_ensemble_score(segment)
            scores.append(score)
            positions.append(start)
        
        scores = np.array(scores)
        
        # Detect peaks in score
        threshold = CORRELATION_THRESHOLD
        detections = self._extract_detections(scores, positions, threshold, 
                                              video_duration, allow_multiple)
        
        return detections
    
    def _compute_ensemble_score(self, segment):
        """
        Compute ensemble similarity score
        
        Returns:
            score between 0 and 1
        """
        scores = []
        weights = []
        
        # MFCC similarity
        if USE_MFCC_ANALYSIS:
            segment_mfcc = AudioProcessor.extract_mfcc_sequence(segment, self.sr)
            mfcc_score = self._compute_mfcc_similarity(segment_mfcc)
            scores.append(mfcc_score)
            weights.append(0.3)
        
        # Mel-spectrogram similarity
        segment_mel = AudioProcessor.compute_mel_spectrogram_normalized(segment, self.sr)
        mel_score = self._compute_mel_similarity(segment_mel)
        scores.append(mel_score)
        weights.append(0.4)
        
        # Energy envelope similarity
        segment_envelope = AudioProcessor.extract_energy_envelope(segment, self.sr)
        envelope_score = self._compute_envelope_similarity(segment_envelope)
        scores.append(envelope_score)
        weights.append(0.2)
        
        # Weighted average
        weights = np.array(weights)
        scores = np.array(scores)
        ensemble_score = np.sum(scores * weights) / np.sum(weights)
        
        return ensemble_score
    
    def _compute_mfcc_similarity(self, segment_mfcc):
        """Compute DTW distance between MFCC sequences"""
        # Ensure same shape for DTW
        if len(segment_mfcc) < len(self.tag_mfcc):
            segment_mfcc = np.vstack([segment_mfcc, 
                                     np.zeros((len(self.tag_mfcc) - len(segment_mfcc), 
                                              segment_mfcc.shape[1]))])
        
        distance = AudioProcessor.dynamic_time_warping(self.tag_mfcc, segment_mfcc[:len(self.tag_mfcc)])
        similarity = 1.0 / (1.0 + distance)
        return similarity
    
    def _compute_mel_similarity(self, segment_mel):
        """Compute correlation between mel-spectrograms"""
        # Ensure same shape
        if segment_mel.shape[1] < self.tag_mel.shape[1]:
            segment_mel = np.hstack([segment_mel, 
                                    np.zeros((segment_mel.shape[0], 
                                            self.tag_mel.shape[1] - segment_mel.shape[1]))])
        
        segment_mel = segment_mel[:, :self.tag_mel.shape[1]]
        
        # Flatten and compute correlation
        tag_flat = self.tag_mel.flatten()
        segment_flat = segment_mel.flatten()
        
        similarity = AudioProcessor.compute_correlation(tag_flat, segment_flat)
        return similarity
    
    def _compute_envelope_similarity(self, segment_envelope):
        """Compute envelope similarity"""
        if len(segment_envelope) < len(self.tag_envelope):
            segment_envelope = np.pad(segment_envelope, 
                                     (0, len(self.tag_envelope) - len(segment_envelope)),
                                     mode='constant')
        
        segment_envelope = segment_envelope[:len(self.tag_envelope)]
        similarity = AudioProcessor.compute_correlation(self.tag_envelope, segment_envelope)
        return similarity
    
    def _extract_detections(self, scores, positions, threshold, duration, allow_multiple):
        """
        Extract detection peaks from score array
        
        Returns:
            list of (start_time, end_time, confidence) tuples
        """
        detections = []
        processed = set()
        
        # Find local maxima
        peaks, properties = signal.find_peaks(scores, height=threshold, 
                                             distance=int(0.5 * self.sr / 100))
        
        for peak_idx in peaks:
            peak_score = scores[peak_idx]
            peak_position = positions[peak_idx]
            
            # Check if this detection is far enough from others
            is_duplicate = False
            for existing_pos in processed:
                if abs(peak_position - existing_pos) < MIN_GAP_BETWEEN_TAGS * self.sr:
                    is_duplicate = True
                    break
            
            if not is_duplicate or allow_multiple:
                start_time = AudioProcessor.samples_to_time(peak_position, self.sr)
                end_time = start_time + self.tag_duration
                
                # Clamp to valid range
                end_time = min(end_time, duration)
                
                detections.append((start_time, end_time, float(peak_score)))
                processed.add(peak_position)
        
        return sorted(detections, key=lambda x: x[0])
