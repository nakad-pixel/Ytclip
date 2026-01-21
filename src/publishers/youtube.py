#!/usr/bin/env python3
"""
YouTube Publisher: Upload clips to YouTube Shorts
Handles authentication, metadata, and upload process.
"""

import os
import logging
from typing import Optional, Dict, Any
import pickle
import json

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubePublisher:
    """Publish clips to YouTube Shorts."""

    def __init__(self, client_secrets_file: Optional[str] = None,
                 credentials_file: str = 'data/youtube_credentials.pickle'):
        """
        Initialize YouTube publisher.

        Args:
            client_secrets_file: Path to OAuth client secrets JSON
            credentials_file: Path to store/load credentials
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API client not installed")

        self.client_secrets_file = client_secrets_file or os.getenv('YOUTUBE_CLIENT_SECRETS')
        self.credentials_file = credentials_file
        self.credentials = None
        self.youtube = None

        # Try to load existing credentials
        self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with YouTube API."""
        # Load credentials from file if available
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'rb') as token:
                self.credentials = pickle.load(token)

        # Refresh or create credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            elif self.client_secrets_file:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES
                )
                self.credentials = flow.run_local_server(port=0)

                # Save credentials
                with open(self.credentials_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
            else:
                logger.warning("No valid credentials and no client secrets file")
                return False

        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        logger.info("Successfully authenticated with YouTube API")
        return True

    def upload_clip(self, clip_path: str, title: str, description: str,
                    tags: list, privacy: str = 'public') -> Optional[str]:
        """
        Upload a clip to YouTube Shorts.

        Args:
            clip_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags/hashtags
            privacy: Video privacy status (public, unlisted, private)

        Returns:
            YouTube video ID if successful, None otherwise
        """
        if not self.youtube:
            logger.error("Not authenticated with YouTube")
            return None

        try:
            # Prepare metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags[:500],  # YouTube allows up to 500 tags
                    'categoryId': '20'  # Gaming category
                },
                'status': {
                    'privacyStatus': privacy,
                    'selfDeclaredMadeForKids': False
                }
            }

            # Prepare media upload
            media = MediaFileUpload(
                clip_path,
                mimetype='video/mp4',
                resumable=True
            )

            # Create upload request
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            logger.info(f"Starting upload: {clip_path}")

            # Upload with progress callback
            response = request.execute()

            video_id = response.get('id')
            if video_id:
                logger.info(f"Successfully uploaded: https://youtube.com/shorts/{video_id}")
                return video_id
            else:
                logger.error("Upload failed: No video ID in response")
                return None

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    def publish_clip(self, clip_data: Dict[str, Any], privacy: str = 'public') -> Optional[Dict[str, Any]]:
        """
        Publish a clip with metadata.

        Args:
            clip_data: Dictionary containing:
                - clip_path: Path to video file
                - metadata: SEO metadata (title, description, hashtags)
                - moment: Original moment data
            privacy: Video privacy status

        Returns:
            Publication result with video ID
        """
        if not os.path.exists(clip_data['clip_path']):
            logger.error(f"Clip not found: {clip_data['clip_path']}")
            return None

        metadata = clip_data.get('metadata', {})
        title = metadata.get('title', 'Viral Gaming Clip')
        description = metadata.get('description', '')
        hashtags = metadata.get('hashtags', [])

        video_id = self.upload_clip(
            clip_path=clip_data['clip_path'],
            title=title,
            description=description,
            tags=hashtags,
            privacy=privacy
        )

        if video_id:
            return {
                'platform': 'youtube',
                'video_id': video_id,
                'url': f"https://youtube.com/shorts/{video_id}",
                'status': 'published'
            }
        else:
            return {
                'platform': 'youtube',
                'status': 'failed'
            }

    def get_video_stats(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a published video."""
        if not self.youtube:
            return None

        try:
            request = self.youtube.videos().list(
                part='statistics',
                id=video_id
            )
            response = request.execute()

            if response.get('items'):
                stats = response['items'][0]['statistics']
                return {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0))
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get video stats: {e}")
            return None

def main():
    """Test YouTube publisher."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python youtube.py <video_path>")
        sys.exit(1)

    clip_path = sys.argv[1]

    publisher = YouTubePublisher()

    # Test upload
    result = publisher.publish_clip({
        'clip_path': clip_path,
        'metadata': {
            'title': 'Test YouTube Short',
            'description': 'This is a test upload',
            'hashtags': ['#test', '#gaming']
        }
    }, privacy='unlisted')

    if result:
        print(f"Published: {result.get('url')}")
    else:
        print("Upload failed")

if __name__ == '__main__':
    main()
