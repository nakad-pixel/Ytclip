#!/usr/bin/env python3
"""
Video Downloader: Download videos from YouTube using yt-dlp
Handles format selection and temporary storage.
"""

import os
import subprocess
import logging
from typing import Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, output_dir: str = 'data/downloads'):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def download(self, video_id: str, quality: str = 'best') -> Optional[str]:
        """
        Download video from YouTube.
        Returns path to downloaded file or None on failure.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = os.path.join(self.output_dir, '%(id)s.%(ext)s')

        cmd = [
            'yt-dlp',
            '-f', 'best[height<=720]',  # Limit to 720p for speed
            '-o', output_template,
            '--quiet',
            '--no-warnings',
            url
        ]

        try:
            logger.info(f"Downloading {video_id}...")
            subprocess.run(cmd, check=True, timeout=300)

            # Find downloaded file
            for ext in ['mp4', 'mkv', 'webm']:
                filepath = os.path.join(self.output_dir, f"{video_id}.{ext}")
                if os.path.exists(filepath):
                    logger.info(f"Downloaded to: {filepath}")
                    return filepath

            logger.error(f"Downloaded file not found for {video_id}")
            return None

        except subprocess.TimeoutExpired:
            logger.error(f"Download timeout for {video_id}")
            return None
        except Exception as e:
            logger.error(f"Download error for {video_id}: {e}")
            return None

    def cleanup(self, filepath: str) -> None:
        """Delete downloaded file."""
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up: {filepath}")
