#!/usr/bin/env python3
"""Main entry point for Audio Tag Detection and Removal System"""

import argparse
import sys
from pathlib import Path
import json
import numpy as np
from tqdm import tqdm
import traceback

from config import *
from file_handler import FileHandler
from audio_utils import AudioProcessor
from tag_detector import TagDetector
from tag_remover import TagRemover


class AudioTagSystem:
    """Main system orchestrator"""
    
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def process_video(self, video_path, tag_audio_path, tag_duration, 
                      new_tag_path=None, new_tag_positions=None, allow_multiple=False):
        """
        Complete processing pipeline
        
        Args:
            video_path: path to input video/audio
            tag_audio_path: path to tag audio file
            tag_duration: duration of tag in seconds
            new_tag_path: path to new tag audio (optional)
            new_tag_positions: list of positions to insert new tags (optional)
            allow_multiple: allow multiple tag detections
            
        Returns:
            dict with processing results
        """
        try:
            print("="*60)
            print("Audio Tag Detection & Removal System")
            print("="*60)
            
            # Validate input files
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            if not Path(tag_audio_path).exists():
                raise FileNotFoundError(f"Tag audio file not found: {tag_audio_path}")
            
            print(f"\n[1/5] Loading audio files...")
            
            # Load video audio
            video_audio, sr, video_format = FileHandler.load_audio_file(video_path, sr=SAMPLE_RATE)
            print(f"  - Video: {len(video_audio)/sr:.2f}s ({sr}Hz)")
            
            # Load tag audio
            tag_audio, _, _ = FileHandler.load_audio_file(tag_audio_path, sr=SAMPLE_RATE)
            print(f"  - Tag: {len(tag_audio)/sr:.2f}s ({sr}Hz)")
            
            # Initialize detector
            print(f"\n[2/5] Initializing tag detector...")
            detector = TagDetector(tag_audio, tag_duration, sr=SAMPLE_RATE)
            
            # Detect tags
            print(f"\n[3/5] Detecting tags in video...")
            detections = detector.detect_tags(video_audio, allow_multiple=allow_multiple)
            
            if not detections:
                print("  - No tags detected!")
                return {
                    'success': False,
                    'message': 'No tags detected in video',
                    'detections': []
                }
            
            print(f"  - Found {len(detections)} tag(s)")
            for i, (start, end, conf) in enumerate(detections, 1):
                print(f"    Tag {i}: {start:.2f}s - {end:.2f}s (confidence: {conf:.3f})")
            
            # Remove tags
            print(f"\n[4/5] Removing tags...")
            cleaned_audio = TagRemover.remove_multiple_tags(video_audio, detections, sr=SAMPLE_RATE)
            
            # Add new tags if provided
            output_audio = cleaned_audio
            if new_tag_path and new_tag_positions:
                print(f"\n[4b/5] Adding new tags...")
                if not Path(new_tag_path).exists():
                    raise FileNotFoundError(f"New tag file not found: {new_tag_path}")
                
                new_tag, _, _ = FileHandler.load_audio_file(new_tag_path, sr=SAMPLE_RATE)
                output_audio = TagRemover.add_multiple_tags(cleaned_audio, new_tag, 
                                                            new_tag_positions, sr=SAMPLE_RATE)
                print(f"  - Added {len(new_tag_positions)} new tag(s)")
            
            # Save output
            print(f"\n[5/5] Saving output file...")
            output_file = FileHandler.save_with_original_name(output_audio, video_path, 
                                                             self.output_dir, SAMPLE_RATE, 
                                                             OUTPUT_BITRATE)
            print(f"  - Saved to: {output_file}")
            
            # Generate report
            report = self._generate_report(video_path, detections, new_tag_positions)
            report_file = self._save_report(report, video_path)
            
            print(f"  - Report saved to: {report_file}")
            print("\n" + "="*60)
            print("Processing completed successfully!")
            print("="*60)
            
            return {
                'success': True,
                'video_path': str(video_path),
                'output_file': str(output_file),
                'detections': detections,
                'new_tags': new_tag_positions if new_tag_positions else [],
                'report_file': str(report_file),
                'message': 'Processing completed successfully'
            }
        
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'message': str(e),
                'error': traceback.format_exc()
            }
        
        finally:
            # Cleanup
            FileHandler.cleanup_temp_files()
    
    def _generate_report(self, video_path, detections, new_tag_positions=None):
        """Generate processing report"""
        report = {
            'input_file': str(video_path),
            'detected_tags': [
                {
                    'index': i,
                    'start_time': round(start, 3),
                    'end_time': round(end, 3),
                    'duration': round(end - start, 3),
                    'confidence': round(conf, 4)
                }
                for i, (start, end, conf) in enumerate(detections, 1)
            ],
            'new_tags': []
        }
        
        if new_tag_positions:
            report['new_tags'] = [
                {
                    'index': i,
                    'position': round(pos, 3)
                }
                for i, pos in enumerate(new_tag_positions, 1)
            ]
        
        return report
    
    def _save_report(self, report, video_path):
        """Save report as text file"""
        video_path = Path(video_path)
        report_file = self.log_dir / f"{video_path.stem}_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("Audio Tag Detection & Removal Report\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Input File: {report['input_file']}\n\n")
            
            f.write("DETECTED TAGS:\n")
            f.write("-" * 70 + "\n")
            if report['detected_tags']:
                f.write(f"{'#':<5} {'Start (s)':<15} {'End (s)':<15} {'Duration (s)':<15} {'Confidence':<10}\n")
                f.write("-" * 70 + "\n")
                for tag in report['detected_tags']:
                    f.write(f"{tag['index']:<5} {tag['start_time']:<15} {tag['end_time']:<15} "
                           f"{tag['duration']:<15} {tag['confidence']:<10.4f}\n")
            else:
                f.write("No tags detected\n")
            
            f.write("\n")
            f.write("NEW TAGS INSERTED:\n")
            f.write("-" * 70 + "\n")
            if report['new_tags']:
                f.write(f"{'#':<5} {'Position (s)':<20}\n")
                f.write("-" * 70 + "\n")
                for tag in report['new_tags']:
                    f.write(f"{tag['index']:<5} {tag['position']:<20}\n")
            else:
                f.write("No new tags inserted\n")
            
            f.write("\n" + "="*70 + "\n")
        
        return report_file


def main():
    parser = argparse.ArgumentParser(
        description='Audio Tag Detection and Removal System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect and remove tags
  python main.py --video input.mp4 --tag tag_sample.wav --duration 2.0
  
  # Detect, remove and replace with new tags
  python main.py --video input.mkv --tag tag_sample.wav --duration 1.5 \
                  --new-tag new_tag.wav --new-positions 5.0 10.5 15.3
  
  # Allow multiple detections
  python main.py --video video.mp4 --tag tag.wav --duration 1.0 --multiple
  
  # Custom output directory
  python main.py --video video.mp4 --tag tag.wav --duration 2.0 --output /path/to/output
        """)
    
    parser.add_argument('--video', '-v', required=True, help='Input video/audio file')
    parser.add_argument('--tag', '-t', required=True, help='Reference tag audio file')
    parser.add_argument('--duration', '-d', type=float, required=True, help='Tag duration in seconds')
    parser.add_argument('--new-tag', '-nt', help='New tag audio file to insert (optional)')
    parser.add_argument('--new-positions', '-np', type=float, nargs='+', 
                       help='Positions (in seconds) to insert new tags (optional)')
    parser.add_argument('--output', '-o', default=str(OUTPUT_DIR), help='Output directory')
    parser.add_argument('--multiple', '-m', action='store_true', help='Allow multiple tag detections')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not FileHandler.is_supported_format(args.video):
        print(f"Error: Unsupported video format. Supported: {SUPPORTED_FORMATS}")
        sys.exit(1)
    
    if not FileHandler.is_supported_format(args.tag):
        print(f"Error: Unsupported tag format. Supported: {SUPPORTED_FORMATS}")
        sys.exit(1)
    
    if args.duration <= 0:
        print("Error: Duration must be positive")
        sys.exit(1)
    
    # Run system
    system = AudioTagSystem(output_dir=args.output)
    result = system.process_video(
        video_path=args.video,
        tag_audio_path=args.tag,
        tag_duration=args.duration,
        new_tag_path=args.new_tag,
        new_tag_positions=args.new_positions,
        allow_multiple=args.multiple
    )
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
