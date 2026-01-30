#!/usr/bin/env python3
"""
Transcription API Module: Fetch captions using YouTube Data API v3
Primary transcription method to avoid bot detection issues.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import json
import time

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    logging.warning("YouTube API client not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeCaptionFetcher:
    """Fetch captions from YouTube using official API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with YouTube API key."""
        if not YOUTUBE_API_AVAILABLE:
            raise ImportError("YouTube API client not installed")
        
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not provided")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        logger.info("Initialized YouTube API client")
    
    def fetch_captions(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch captions for a video using YouTube API."""
        try:
            # Get caption tracks
            caption_list = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()
            
            if not caption_list.get('items'):
                logger.info(f"No captions available for video {video_id}")
                return None
            
            # Find English auto-generated captions (most common)
            caption_track = None
            for item in caption_list['items']:
                if item['snippet'].get('trackKind') == 'asr':  # Auto-generated
                    caption_track = item
                    break
            
            if not caption_track:
                # Fallback to any caption track
                caption_track = caption_list['items'][0]
            
            # Download caption track
            caption_id = caption_track['id']
            caption = self.youtube.captions().download(
                id=caption_id,
                tfmt='json3'  # JSON format with timestamps
            ).execute()
            
            # Parse caption data
            transcription = self._parse_caption_data(caption, video_id)
            return transcription
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"Captions not available for video {video_id} (403)")
            elif e.resp.status == 404:
                logger.warning(f"Video {video_id} not found (404)")
            else:
                logger.error(f"YouTube API error for {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching captions for {video_id}: {e}")
            return None
    
    def _parse_caption_data(self, caption_data: str, video_id: str) -> Dict[str, Any]:
        """Parse YouTube caption JSON format to match Whisper output structure."""
        try:
            # Parse the caption data (it's a JSON string)
            captions = json.loads(caption_data)
            
            # Extract segments with timestamps
            segments = []
            full_text = []
            
            for caption in captions.get('events', []):
                if 'segs' in caption:
                    text = ''.join(seg['utf8'] for seg in caption['segs'])
                    start_time = caption['tStartMs'] / 1000.0  # Convert ms to seconds
                    end_time = start_time + (caption.get('dDurationMs', 1000) / 1000.0)
                    
                    segment = {
                        'start': start_time,
                        'end': end_time,
                        'text': text.strip(),
                        'words': []  # We'll populate this below
                    }
                    segments.append(segment)
                    full_text.append(text)
            
            # Create words list for compatibility with existing code
            words = []
            for segment in segments:
                # Simple word splitting - YouTube captions don't provide word-level timestamps
                segment_words = segment['text'].split()
                for word_text in segment_words:
                    words.append({
                        'word': word_text,
                        'start': segment['start'],
                        'end': segment['end']
                    })
                segment['words'] = words[len(words) - len(segment_words):]
            
            # Calculate total duration
            duration = segments[-1]['end'] if segments else 0
            
            return {
                'segments': segments,
                'text': ' '.join(full_text).strip(),
                'language': 'en',  # YouTube captions are typically English
                'duration': duration,
                'source': 'youtube_captions',
                'video_id': video_id
            }
            
        except Exception as e:
            logger.error(f"Error parsing caption data for {video_id}: {e}")
            return {
                'segments': [],
                'text': '',
                'language': 'en',
                'duration': 0,
                'source': 'youtube_captions',
                'video_id': video_id
            }
    
    def check_caption_availability(self, video_id: str) -> bool:
        """Check if captions are available for a video."""
        try:
            caption_list = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()
            return bool(caption_list.get('items'))
        except HttpError as e:
            if e.resp.status == 403:
                return False
            raise
        except Exception as e:
            logger.error(f"Error checking caption availability: {e}")
            return False