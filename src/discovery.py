#!/usr/bin/env python3
"""
Discovery Module: Identify trending gaming videos from YouTube
Searches multiple niches and filters by quality metrics.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from googleapiclient.discovery import build
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
NICHES = ['Roblox', 'Horror games', 'Fortnite']
MIN_VIEWS = 10000
SEARCH_ORDER = 'viewCount'
MAX_RESULTS = 50
API_QUOTA_LIMIT = 1000  # Reserve quota

class DiscoveryService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.db_path = 'data/videos.db'
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for tracking processed videos."""
        os.makedirs('data', exist_ok=True)
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

    def search_niche(self, niche: str) -> List[Dict[str, Any]]:
        """Search for trending videos in a specific niche."""
        try:
            request = self.youtube.search().list(
                q=niche,
                part='snippet',
                type='video',
                order=SEARCH_ORDER,
                maxResults=MAX_RESULTS,
                publishedAfter=(datetime.now() - timedelta(days=7)).isoformat() + 'Z',
                regionCode='US',
                relevanceLanguage='en'
            )
            response = request.execute()
            videos = []

            for item in response.get('items', []):
                video_id = item['id']['videoId']
                videos.append({
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'niche': niche
                })

            logger.info(f"Found {len(videos)} videos in niche: {niche}")
            return videos

        except Exception as e:
            logger.error(f"Error searching niche {niche}: {e}")
            return []

    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Fetch detailed video statistics."""
        try:
            request = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.warning(f"No details found for video {video_id}")
                return {}
                
            item = response['items'][0]
            stats = item['statistics']
            details = item['contentDetails']

            return {
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
                'duration': details.get('duration', 'PT0S')
            }

        except Exception as e:
            logger.error(f"Error fetching details for {video_id}: {e}")
            return {}

    def is_already_processed(self, video_id: str) -> bool:
        """Check if video has already been processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT processed FROM videos WHERE youtube_id = ?', (video_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0]

    def save_video(self, video_id: str, metadata: Dict[str, Any]) -> None:
        """Save discovered video to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
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
            logger.info(f"Saved video to database: {video_id}")
        except sqlite3.IntegrityError:
            logger.debug(f"Video {video_id} already in database")
        finally:
            conn.close()

    def run(self) -> List[str]:
        """Execute full discovery pipeline."""
        discovered_videos = []

        for niche in NICHES:
            logger.info(f"Searching niche: {niche}")
            videos = self.search_niche(niche)

            for video in videos:
                video_id = video['video_id']

                # Skip if already processed
                if self.is_already_processed(video_id):
                    logger.info(f"Skipping already-processed video: {video_id}")
                    continue

                # Get detailed stats
                details = self.get_video_details(video_id)
                if not details:
                    logger.warning(f"Skipping video {video_id}: no details available")
                    continue
                    
                video.update(details)

                # Filter by minimum views
                if video['view_count'] < MIN_VIEWS:
                    logger.debug(f"Skipping video {video_id}: {video['view_count']} views < {MIN_VIEWS}")
                    continue

                # Save and track
                self.save_video(video_id, video)
                discovered_videos.append(video_id)
                logger.info(f"Discovered: {video['title']} ({video['view_count']} views)")

        logger.info(f"Total discovered: {len(discovered_videos)} unique videos")
        return discovered_videos

def main():
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        logger.error("YOUTUBE_API_KEY environment variable not set")
        # Set empty outputs for GitHub Actions
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"videos=[]\n")
                f.write(f"video_count=0\n")
        raise ValueError("YOUTUBE_API_KEY environment variable not set")

    service = DiscoveryService(api_key)
    videos = service.run()

    # Save to file
    os.makedirs('data', exist_ok=True)
    with open('data/discovered_videos.json', 'w') as f:
        json.dump(videos, f, indent=2)

    # Output for GitHub Actions
    # CRITICAL FIX: Output as JSON array directly for matrix strategy
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            # Output the array in the correct format for matrix
            videos_json = json.dumps(videos)
            f.write(f"videos={videos_json}\n")
            f.write(f"video_count={len(videos)}\n")
            logger.info(f"Set GitHub Actions output: {len(videos)} videos")
    else:
        logger.warning("GITHUB_OUTPUT environment variable not set")

    # Also output to stdout for debugging
    print(f"\nDiscovery Summary:")
    print(f"Videos discovered: {len(videos)}")
    print(f"Video IDs: {videos}")
    
    logger.info("Discovery complete")

if __name__ == '__main__':
    main()
