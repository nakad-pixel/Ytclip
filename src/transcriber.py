#!/usr/bin/env python3
"""
Transcriber Module: Extract audio and transcribe using Whisper
Converts video audio to timestamped text for analysis.
"""

import os
import logging
import subprocess
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available, transcription will be disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, model_size: str = 'base'):
        """
        Initialize transcriber with Whisper model.
        Model sizes: tiny, base, small, medium, large
        """
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper package not installed. Run: pip install openai-whisper")

        self.model = whisper.load_model(model_size)
        logger.info(f"Loaded Whisper model: {model_size}")

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Extract audio from video file using FFmpeg."""
        if output_path is None:
            output_path = video_path.rsplit('.', 1)[0] + '.wav'

        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz sample rate for Whisper
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                output_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted audio to: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio: {e.stderr.decode()}")
            return None

    def transcribe(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio file using Whisper."""
        try:
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                fp16=False  # Use FP32 for better compatibility
            )

            logger.info(f"Transcribed {len(result['segments'])} segments")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    def process_video(self, video_path: str, keep_audio: bool = False) -> Optional[Dict[str, Any]]:
        """
        Full pipeline: extract audio and transcribe.
        Returns transcription result with timestamps.
        """
        # Extract audio
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return None

        try:
            # Transcribe
            result = self.transcribe(audio_path)

            if result:
                # Add audio path to result for reference
                result['audio_path'] = audio_path

            return result

        finally:
            # Cleanup audio file if not keeping it
            if not keep_audio and os.path.exists(audio_path):
                os.remove(audio_path)
                logger.debug(f"Cleaned up audio: {audio_path}")

    def get_text_segments(self, transcription: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract text segments with timestamps from transcription."""
        segments = []
        for seg in transcription.get('segments', []):
            segments.append({
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip(),
                'words': seg.get('words', [])
            })
        return segments

    def find_segments_by_keywords(self, transcription: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """Find segments containing specific keywords."""
        matching_segments = []
        segments = self.get_text_segments(transcription)

        for seg in segments:
            text_lower = seg['text'].lower()
            if any(keyword.lower() in text_lower for keyword in keywords):
                matching_segments.append(seg)

        logger.info(f"Found {len(matching_segments)} segments matching keywords")
        return matching_segments

def main():
    """Test transcriber with a video file."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    transcriber = Transcriber(model_size='base')
    result = transcriber.process_video(video_path)

    if result:
        print(f"\nTranscription:")
        print(f"Language: {result.get('language', 'unknown')}")
        print(f"Duration: {result.get('duration', 0):.2f}s")
        print(f"\nFull text:\n{result['text']}\n")

        print("\nSegments:")
        for seg in result['segments'][:5]:  # Show first 5 segments
            print(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
    else:
        print("Transcription failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
