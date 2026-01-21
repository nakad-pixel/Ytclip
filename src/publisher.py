#!/usr/bin/env python3
"""
Publisher Module: Orchestrate publishing to all platforms
Manages multi-platform upload with rate limiting and error handling.
"""

import os
import logging
from typing import List, Dict, Any
import time

from .publishers.youtube import YouTubePublisher
from .publishers.tiktok import TikTokPublisher
from .publishers.instagram import InstagramPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Publisher:
    """Orchestrate publishing to multiple platforms."""

    def __init__(self, platforms: List[str] = None,
                 stagger_minutes: int = 120):
        """
        Initialize publisher.

        Args:
            platforms: List of platforms to publish to
            stagger_minutes: Minutes to wait between platform uploads
        """
        self.platforms = platforms or ['youtube', 'tiktok', 'instagram']
        self.stagger_minutes = stagger_minutes

        # Initialize platform publishers
        self.publishers = {}
        if 'youtube' in self.platforms:
            try:
                self.publishers['youtube'] = YouTubePublisher()
            except Exception as e:
                logger.warning(f"Could not initialize YouTube publisher: {e}")

        if 'tiktok' in self.platforms:
            try:
                self.publishers['tiktok'] = TikTokPublisher()
            except Exception as e:
                logger.warning(f"Could not initialize TikTok publisher: {e}")

        if 'instagram' in self.platforms:
            try:
                self.publishers['instagram'] = InstagramPublisher()
            except Exception as e:
                logger.warning(f"Could not initialize Instagram publisher: {e}")

    def publish_clip(self, clip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a clip to all configured platforms.

        Args:
            clip_data: Dictionary containing:
                - clip_path: Path to video file (can be different per platform)
                - metadata: SEO metadata
                - moment: Original moment data

        Returns:
            Dictionary with results from each platform
        """
        results = {
            'platforms': {},
            'success_count': 0,
            'total_count': 0
        }

        for platform_name, publisher in self.publishers.items():
            try:
                logger.info(f"Publishing to {platform_name}...")

                # Check if platform-specific clip exists
                platform_clip_path = clip_data.get(f'{platform_name}_path') or clip_data.get('clip_path')

                clip_for_platform = {
                    'clip_path': platform_clip_path,
                    'metadata': clip_data.get('metadata', {}),
                    'moment': clip_data.get('moment', {})
                }

                result = publisher.publish_clip(clip_for_platform)

                if result:
                    results['platforms'][platform_name] = result
                    if result.get('status') == 'published':
                        results['success_count'] += 1
                        logger.info(f"Successfully published to {platform_name}")
                    else:
                        logger.warning(f"Failed to publish to {platform_name}")
                else:
                    results['platforms'][platform_name] = {'status': 'failed'}

                results['total_count'] += 1

                # Stagger uploads if configured
                if self.stagger_minutes > 0 and platform_name != list(self.publishers.keys())[-1]:
                    logger.info(f"Waiting {self.stagger_minutes} minutes before next upload...")
                    time.sleep(self.stagger_minutes * 60)

            except Exception as e:
                logger.error(f"Error publishing to {platform_name}: {e}")
                results['platforms'][platform_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['total_count'] += 1

        return results

    def publish_clips_batch(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Publish multiple clips in batch.

        Args:
            clips: List of clip data dictionaries

        Returns:
            List of publication results
        """
        results = []

        for i, clip_data in enumerate(clips, 1):
            logger.info(f"Processing clip {i}/{len(clips)}")
            result = self.publish_clip(clip_data)
            results.append(result)

        return results

def main():
    """Test publisher with a clip."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python publisher.py <video_path>")
        sys.exit(1)

    clip_data = {
        'clip_path': sys.argv[1],
        'metadata': {
            'title': 'Test Viral Clip',
            'description': 'This is a test upload from AutoClip Gaming',
            'hashtags': ['#gaming', '#viral', '#test']
        }
    }

    publisher = Publisher()
    results = publisher.publish_clip(clip_data)

    print(f"\nResults:")
    print(f"Success: {results['success_count']}/{results['total_count']}")
    for platform, result in results['platforms'].items():
        url = result.get('url', 'N/A')
        print(f"  {platform}: {result['status']} ({url})")

if __name__ == '__main__':
    main()
