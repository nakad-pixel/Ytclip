#!/usr/bin/env python3
"""
Editor Module: Process videos and extract clips using FFmpeg
Handles resizing, cropping, and format conversion for social platforms.
"""

import os
import logging
import subprocess
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Platform-specific settings
PLATFORM_SETTINGS = {
    'youtube_shorts': {
        'width': 1080,
        'height': 1920,
        'fps': 30,
        'max_duration': 60,
        'codec': 'libx264',
        'audio_codec': 'aac',
        'bitrate': '3M',
        'audio_bitrate': '128k'
    },
    'tiktok': {
        'width': 1080,
        'height': 1920,
        'fps': 30,
        'max_duration': 600,
        'codec': 'libx264',
        'audio_codec': 'aac',
        'bitrate': '4M',
        'audio_bitrate': '128k'
    },
    'instagram_reels': {
        'width': 1080,
        'height': 1920,
        'fps': 30,
        'max_duration': 90,
        'codec': 'libx264',
        'audio_codec': 'aac',
        'bitrate': '3.5M',
        'audio_bitrate': '128k'
    }
}

class VideoEditor:
    """Edit and process videos for social media platforms."""

    def __init__(self, output_dir: str = 'data/clips'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_clip(self, video_path: str, start_time: float, end_time: float,
                     output_path: Optional[str] = None) -> Optional[str]:
        """
        Extract a clip from video at specified timestamps.
        """
        if output_path is None:
            video_id = Path(video_path).stem
            output_path = str(self.output_dir / f"{video_id}_{start_time:.0f}-{end_time:.0f}.mp4")

        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-c', 'copy',  # Fast copy without re-encoding
                '-avoid_negative_ts', '1',
                '-y',
                output_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted clip: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract clip: {e.stderr.decode()}")
            return None

    def resize_to_vertical(self, input_path: str, platform: str = 'youtube_shorts',
                           output_path: Optional[str] = None) -> Optional[str]:
        """
        Resize and crop video to vertical format (9:16) for social platforms.
        """
        settings = PLATFORM_SETTINGS.get(platform, PLATFORM_SETTINGS['youtube_shorts'])

        if output_path is None:
            input_stem = Path(input_path).stem
            ext = Path(input_path).suffix
            output_path = str(self.output_dir / f"{input_stem}_{platform}{ext}")

        try:
            # Get video info first
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'json',
                input_path
            ]

            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            info = json.loads(result.stdout)
            streams = info.get('streams', [])
            if not streams:
                logger.error("Could not get video dimensions")
                return None

            original_width = int(streams[0]['width'])
            original_height = int(streams[0]['height'])

            # Calculate crop dimensions to center the content
            # For vertical video (9:16), we want to crop to maintain aspect ratio
            target_aspect = settings['height'] / settings['width']
            video_aspect = original_height / original_width

            if video_aspect > target_aspect:
                # Video is already tall enough, crop top/bottom
                crop_height = int(original_width * target_aspect)
                crop_y = int((original_height - crop_height) / 2)
                crop_filter = f"crop={original_width}:{crop_height}:0:{crop_y},scale={settings['width']}:{settings['height']}"
            else:
                # Video needs horizontal crop
                crop_width = int(original_height / target_aspect)
                crop_x = int((original_width - crop_width) / 2)
                crop_filter = f"crop={crop_width}:{original_height}:{crop_x}:0,scale={settings['width']}:{settings['height']}"

            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', crop_filter,
                '-c:v', settings['codec'],
                '-b:v', settings['bitrate'],
                '-c:a', settings['audio_codec'],
                '-b:a', settings['audio_bitrate'],
                '-r', str(settings['fps']),
                '-movflags', '+faststart',
                '-y',
                output_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Resized to {platform}: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to resize video: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Error resizing video: {e}")
            return None

    def process_clip_for_platform(self, video_path: str, start_time: float, end_time: float,
                                   platform: str) -> Optional[str]:
        """
        Full pipeline: extract clip and convert to platform-specific format.
        """
        # First extract raw clip
        raw_clip = self.extract_clip(video_path, start_time, end_time)
        if not raw_clip:
            return None

        try:
            # Convert to platform format
            final_clip = self.resize_to_vertical(raw_clip, platform)

            # Cleanup raw clip
            if os.path.exists(raw_clip) and raw_clip != final_clip:
                os.remove(raw_clip)

            return final_clip

        except Exception as e:
            logger.error(f"Failed to process clip for {platform}: {e}")
            return None

    def batch_process_moments(self, video_path: str, moments: List[Dict[str, Any]],
                             platforms: List[str] = None) -> List[Dict[str, Any]]:
        """
        Process multiple moments for multiple platforms.
        Returns list of generated clips with metadata.
        """
        if platforms is None:
            platforms = ['youtube_shorts', 'tiktok', 'instagram_reels']

        generated_clips = []

        for moment in moments:
            for platform in platforms:
                clip_path = self.process_clip_for_platform(
                    video_path,
                    moment['start'],
                    moment['end'],
                    platform
                )

                if clip_path:
                    generated_clips.append({
                        'platform': platform,
                        'clip_path': clip_path,
                        'start_time': moment['start'],
                        'end_time': moment['end'],
                        'type': moment['type'],
                        'quote': moment['quote'],
                        'virality_score': moment['virality_score']
                    })
                    logger.info(f"Generated {platform} clip: {clip_path}")

        return generated_clips

    def add_captions(self, video_path: str, captions: List[Dict[str, Any]],
                     output_path: Optional[str] = None,
                     style: str = 'gaming') -> Optional[str]:
        """
        Burn captions into video using FFmpeg drawtext filter.
        """
        if not captions:
            logger.warning("No captions to add")
            return video_path

        if output_path is None:
            input_stem = Path(video_path).stem
            output_path = str(self.output_dir / f"{input_stem}_captioned.mp4")

        # Style settings
        style_settings = {
            'gaming': {
                'fontcolor': 'yellow',
                'fontsize': 48,
                'bordercolor': 'black',
                'borderw': 3,
                'shadowcolor': 'black@0.5',
                'shadowx': 2,
                'shadowy': 2
            },
            'clean': {
                'fontcolor': 'white',
                'fontsize': 40,
                'bordercolor': 'black',
                'borderw': 2
            }
        }

        s = style_settings.get(style, style_settings['clean'])

        try:
            # Build drawtext filter for each caption
            filter_complex = []
            for i, cap in enumerate(captions):
                # Escape special characters in text
                text = cap['text'].replace(':', '\\:').replace("'", "\\'")

                filter_part = (
                    f"drawtext=text='{text}':"
                    f"fontsize={s['fontsize']}:"
                    f"fontcolor={s['fontcolor']}:"
                    f"bordercolor={s['bordercolor']}:"
                    f"borderw={s['borderw']}:"
                    f"x=(w-tw)/2:y=(h-text_h)*0.85:"
                    f"enable='between(t,{cap['start']},{cap['end']})'"
                )

                filter_complex.append(filter_part)

            # Combine all filters
            vf = ','.join(filter_complex)

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', vf,
                '-c:a', 'copy',
                '-y',
                output_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Added captions: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add captions: {e.stderr.decode()}")
            return None

    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            return duration

        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            return None

def main():
    """Test editor with a video file."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python editor.py <video_path> [start_time] [end_time]")
        sys.exit(1)

    video_path = sys.argv[1]

    editor = VideoEditor()

    # Test clip extraction
    if len(sys.argv) >= 4:
        start = float(sys.argv[2])
        end = float(sys.argv[3])

        clip = editor.extract_clip(video_path, start, end)
        if clip:
            print(f"Extracted clip: {clip}")

            # Test resizing
            resized = editor.resize_to_vertical(clip, 'youtube_shorts')
            if resized:
                print(f"Resized clip: {resized}")
    else:
        duration = editor.get_video_duration(video_path)
        print(f"Video duration: {duration:.2f}s")

if __name__ == '__main__':
    main()
