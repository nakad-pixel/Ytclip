#!/usr/bin/env python3
"""
Discovery Module: Identify trending gaming videos from YouTube
Searches multiple niches and filters by quality metrics.
"""

import os
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
NICHES = ['Roblox', 'Horror games', 'Fortnite']
MIN_VIEWS = 10000
SEARCH_ORDER = 'viewCount'
MAX_RESULTS = 50
API_QUOTA_LIMIT = 1000

class DiscoveryService:
    def __init__(self, api_key: str):
        # CRITICAL: Validate API key before proceeding
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is not set!")
        
        if api_key.strip() == "":
            raise ValueError("YOUTUBE_API_KEY is empty!")
        
        self.api_key = api_key
        self.db_path = 'data/videos.db'
        self.output_path = 'data/discovered_videos.json'
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        logger.info(f"Created/verified data directory")
        
        # Initialize database
        self._init_db()
        
        # Initialize YouTube API
        try:
            logger.info("Initializing YouTube API...")
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            # Test connection with a simple query
            self._test_api_connection()
            logger.info("✓ YouTube API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API: {str(e)}")
            raise

    def _test_api_connection(self):
        """Test that API key is valid."""
        try:
            logger.info("Testing YouTube API connection...")
            request = self.youtube.search().list(
                q="test",
                part="snippet",
                maxResults=1,
                order="relevance"
            )
            response = request.execute()
            logger.info("✓ YouTube API connection successful")
        except HttpError as e:
            if 'disabled' in str(e).lower():
                raise ValueError("YouTube Data API is disabled for this API key")
            elif 'invalid' in str(e).lower():
                raise ValueError("Invalid YouTube API key")
            else:
                raise ValueError(f"YouTube API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Could not connect to YouTube API: {str(e)}")

    def _init_db(self):
        """Initialize SQLite database for tracking processed videos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    youtube_id TEXT UNIQUE,
                    title TEXT,
                    channel TEXT,
                    view_count INTEGER,
                    published_at TEXT,
                    niche TEXT,
                    processed BOOLEAN DEFAULT 0,
                    discovered_at TEXT,
                    url TEXT
                )
            ''')
            conn.commit()
            conn.close()
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def search_niche(self, niche: str) -> List[Dict[str, Any]]:
        """Search for videos in a specific niche."""
        try:
            logger.info(f"Searching for '{niche}' videos...")
            request = self.youtube.search().list(
                q=niche,
                part='snippet',
                type='video',
                order=SEARCH_ORDER,
                maxResults=MAX_RESULTS,
                publishedAfter=(datetime.now() - timedelta(days=7)).isoformat() + 'Z'
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                published_at = item['snippet']['publishedAt']
                
                videos.append({
                    'youtube_id': video_id,
                    'title': title,
                    'channel': channel,
                    'published_at': published_at,
                    'niche': niche,
                    'url': f"https://www.youtube.com/watch?v={video_id}"
                })
            
            logger.info(f"Found {len(videos)} videos for niche: {niche}")
            return videos
        
        except Exception as e:
            logger.error(f"Error searching for {niche}: {str(e)}")
            return []

    def get_video_stats(self, video_id: str) -> Dict[str, Any]:
        """Get view count and other stats for a video."""
        try:
            request = self.youtube.videos().list(
                id=video_id,
                part='statistics,contentDetails'
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                return {
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'duration': item['contentDetails']['duration'],
                    'published_at': item['snippet']['publishedAt']
                }
            return {'view_count': 0}
        
        except Exception as e:
            logger.error(f"Error getting stats for {video_id}: {e}")
            return {'view_count': 0}

    def is_already_processed(self, video_id: str) -> bool:
        """Check if video has already been processed."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT processed FROM videos WHERE youtube_id = ?', (video_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0]
        except Exception as e:
            logger.error(f"Error checking processed status for {video_id}: {e}")
            return False

    def save_video(self, video_id: str, metadata: Dict[str, Any]) -> None:
        """Save discovered video to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO videos
                (youtube_id, title, channel, view_count, published_at, niche, discovered_at, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                metadata['title'],
                metadata['channel'],
                metadata['view_count'],
                metadata['published_at'],
                metadata['niche'],
                datetime.now().isoformat(),
                f"https://www.youtube.com/watch?v={video_id}"
            ))
            conn.commit()
            conn.close()
            logger.debug(f"Video {video_id} saved to database")
        except Exception as e:
            logger.error(f"Error saving video {video_id}: {e}")

    def discover_videos(self) -> List[Dict[str, Any]]:
        """Discover trending gaming videos across all niches."""
        all_videos = []
        
        for niche in NICHES:
            try:
                videos = self.search_niche(niche)
                all_videos.extend(videos)
            except Exception as e:
                logger.error(f"Error processing niche {niche}: {e}")
                continue
        
        if not all_videos:
            logger.warning("No videos discovered across any niche")
            return []
        
        logger.info(f"Total videos discovered: {len(all_videos)}")
        
        # Filter by view count and processed status
        filtered = []
        for video in all_videos:
            video_id = video['youtube_id']
            
            # Skip if already processed
            if self.is_already_processed(video_id):
                logger.info(f"Skipping already-processed video: {video_id}")
                continue
            
            # Get detailed stats
            stats = self.get_video_stats(video_id)
            video.update(stats)
            
            # Filter by minimum views
            if video['view_count'] >= MIN_VIEWS:
                self.save_video(video_id, video)
                filtered.append(video)
                logger.info(f"Added: {video['title']} ({video['view_count']} views)")
            else:
                logger.debug(f"Skipped {video_id}: {video['view_count']} views < {MIN_VIEWS}")
        
        logger.info(f"After filtering (min {MIN_VIEWS} views): {len(filtered)} videos")
        return filtered

    def save_results(self, videos: List[Dict[str, Any]]) -> bool:
        """Save discovered videos to JSON file."""
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(videos, f, indent=2)
            logger.info(f"✓ Saved {len(videos)} videos to {self.output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False

def main():
    """Main discovery function."""
    logger.info("="*60)
    logger.info("YouTube Discovery Service Started")
    logger.info("="*60)
    
    # Get API key from environment
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    # Validate API key
    if not api_key:
        logger.error("❌ YOUTUBE_API_KEY environment variable not set!")
        logger.error("Please set the YOUTUBE_API_KEY secret in GitHub Actions")
        sys.exit(1)
    
    try:
        # Initialize service
        service = DiscoveryService(api_key)
        
        # Discover videos
        logger.info("Starting discovery...")
        videos = service.discover_videos()
        
        # Save results
        if videos:
            service.save_results(videos)
            logger.info(f"✓ SUCCESS: Discovered {len(videos)} videos")
            print(json.dumps([v['youtube_id'] for v in videos]))  # ← OUTPUT FOR GITHUB ACTIONS
        else:
            logger.warning("No videos discovered")
            service.save_results([])
            print(json.dumps([]))  # ← OUTPUT EMPTY ARRAY
        
        logger.info("="*60)
        logger.info("Discovery Complete")
        logger.info("="*60)
        sys.exit(0)
    
    except ValueError as e:
        logger.error(f"❌ Configuration Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()