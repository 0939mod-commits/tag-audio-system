"""File I/O handling for various audio formats"""
import os
import subprocess
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import shutil
from tqdm import tqdm

from config import *


class FileHandler:
    """Handle file operations and format conversions"""
    
    @staticmethod
    def extract_audio_from_video(video_path, temp_dir=TEMP_DIR):
        """
        Extract audio from video file (MP4, MKV)
        
        Args:
            video_path: path to video file
            temp_dir: directory to store extracted audio
            
        Returns:
            path to extracted audio file
        """
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_audio = temp_dir / f"temp_audio_{os.getpid()}.wav"
        
        try:
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-q:a', '9',
                '-n',
                str(temp_audio)
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            return temp_audio
        except Exception as e:
            raise Exception(f"Error extracting audio from video: {str(e)}")
    
    @staticmethod
    def is_supported_format(file_path):
        """Check if file format is supported"""
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_FORMATS
    
    @staticmethod
    def load_audio_file(file_path, sr=SAMPLE_RATE):
        """
        Load audio from any supported format
        
        Args:
            file_path: path to audio/video file
            sr: sample rate
            
        Returns:
            tuple of (audio_array, sample_rate, original_format)
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext in ['.mp4', '.mkv']:
            # Extract audio from video
            temp_audio = FileHandler.extract_audio_from_video(file_path)
            y, sr_loaded = librosa.load(str(temp_audio), sr=sr, mono=True)
            os.remove(temp_audio)
        else:
            # Load audio directly
            y, sr_loaded = librosa.load(str(file_path), sr=sr, mono=True)
        
        return y, sr_loaded, ext
    
    @staticmethod
    def save_audio_file(audio, output_path, sr=SAMPLE_RATE, bitrate=OUTPUT_BITRATE, 
                       format=OUTPUT_FORMAT):
        """
        Save audio to file with specified format and bitrate
        
        Args:
            audio: numpy array of audio
            output_path: output file path
            sr: sample rate
            bitrate: output bitrate (e.g., '128k')
            format: output format (aac, mp3, wav)
            
        Returns:
            path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as temporary WAV first
        temp_wav = output_path.parent / f"temp_{output_path.stem}.wav"
        sf.write(str(temp_wav), audio, sr)
        
        try:
            if format.lower() in ['aac', 'mp3']:
                # Convert to target format with ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', str(temp_wav),
                    '-b:a', bitrate,
                    '-y',
                    str(output_path)
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                os.remove(temp_wav)
            elif format.lower() == 'wav':
                # Keep as WAV
                os.rename(temp_wav, output_path)
            
            return output_path
        except Exception as e:
            if temp_wav.exists():
                os.remove(temp_wav)
            raise Exception(f"Error saving audio file: {str(e)}")
    
    @staticmethod
    def save_with_original_name(audio, input_path, output_dir=OUTPUT_DIR, 
                               sr=SAMPLE_RATE, bitrate=OUTPUT_BITRATE):
        """
        Save audio with same name as input, with AAC format
        
        Args:
            audio: numpy array of audio
            input_path: original input file path
            output_dir: output directory
            sr: sample rate
            bitrate: output bitrate
            
        Returns:
            path to saved file
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use original filename but with .aac extension
        output_file = output_dir / f"{input_path.stem}.aac"
        
        return FileHandler.save_audio_file(audio, output_file, sr, bitrate, 'aac')
    
    @staticmethod
    def cleanup_temp_files(temp_dir=TEMP_DIR):
        """Clean up temporary files"""
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
