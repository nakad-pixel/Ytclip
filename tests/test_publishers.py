#!/usr/bin/env python3
"""
Tests for Publisher Modules
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishers.youtube import YouTubePublisher
from publishers.tiktok import TikTokPublisher
from publishers.instagram import InstagramPublisher
from unittest.mock import Mock, patch, MagicMock

# YouTube Publisher Tests

@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API."""
    with patch('publishers.youtube.build') as mock_build:
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        yield mock_youtube

@pytest.fixture
def youtube_publisher(mock_youtube_api):
    """Create YouTube publisher with mocked API."""
    with patch.dict(os.environ, {'YOUTUBE_CLIENT_SECRETS': 'test.json'}):
        publisher = YouTubePublisher()
        publisher.youtube = mock_youtube_api
        return publisher

def test_upload_clip(youtube_publisher, mock_youtube_api):
    """Test uploading clip to YouTube."""
    mock_youtube_api.videos().insert().execute.return_value = {
        'id': 'yt_test123'
    }

    video_id = youtube_publisher.upload_clip(
        'test.mp4',
        'Test Title',
        'Test Description',
        ['#tag1', '#tag2']
    )

    assert video_id == 'yt_test123'
    assert mock_youtube_api.videos().insert.called

def test_publish_clip(youtube_publisher, mock_youtube_api):
    """Test publishing clip with metadata."""
    mock_youtube_api.videos().insert().execute.return_value = {
        'id': 'yt_test123'
    }

    clip_data = {
        'clip_path': 'test.mp4',
        'metadata': {
            'title': 'Test Clip',
            'description': 'Test Description',
            'hashtags': ['#gaming', '#viral']
        }
    }

    result = youtube_publisher.publish_clip(clip_data)

    assert result['status'] == 'published'
    assert result['platform'] == 'youtube'
    assert result['video_id'] == 'yt_test123'

def test_get_video_stats(youtube_publisher, mock_youtube_api):
    """Test fetching video statistics."""
    mock_youtube_api.videos().list().execute.return_value = {
        'items': [{
            'statistics': {
                'viewCount': '1000',
                'likeCount': '100',
                'commentCount': '10'
            }
        }]
    }

    stats = youtube_publisher.get_video_stats('yt_test123')

    assert stats['views'] == 1000
    assert stats['likes'] == 100
    assert stats['comments'] == 10

# TikTok Publisher Tests

@pytest.fixture
def tiktok_publisher():
    """Create TikTok publisher."""
    return TikTokPublisher()

def test_tiktok_upload_clip(tiktok_publisher):
    """Test TikTok upload (mocked)."""
    video_id = tiktok_publisher.upload_clip(
        'test.mp4',
        'Test Caption',
        ['#gaming'],
        'public'
    )

    # Returns mock ID since TikTok API is restricted
    assert video_id == 'mock_tiktok_video_id'

def test_tiktok_publish_clip(tiktok_publisher):
    """Test publishing to TikTok."""
    clip_data = {
        'clip_path': 'test.mp4',
        'metadata': {
            'title': 'Test TikTok',
            'description': 'Test',
            'hashtags': ['#gaming']
        }
    }

    result = tiktok_publisher.publish_clip(clip_data)

    assert result['platform'] == 'tiktok'
    assert result['status'] == 'published'

# Instagram Publisher Tests

@pytest.fixture
def instagram_publisher():
    """Create Instagram publisher."""
    return InstagramPublisher()

def test_instagram_upload_clip(instagram_publisher):
    """Test Instagram upload (mocked)."""
    media_id = instagram_publisher.upload_clip(
        'test.mp4',
        'Test Caption',
        ['#gaming']
    )

    # Returns mock ID since Instagram API requires review
    assert media_id == 'mock_instagram_media_id'

def test_instagram_publish_clip(instagram_publisher):
    """Test publishing to Instagram."""
    clip_data = {
        'clip_path': 'test.mp4',
        'metadata': {
            'title': 'Test Reel',
            'description': 'Test',
            'hashtags': ['#gaming']
        }
    }

    result = instagram_publisher.publish_clip(clip_data)

    assert result['platform'] == 'instagram'
    assert result['status'] == 'published'
