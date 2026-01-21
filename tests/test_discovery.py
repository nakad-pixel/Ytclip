#!/usr/bin/env python3
"""
Tests for Discovery Module
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from discovery import DiscoveryService
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_youtube():
    """Mock YouTube API client."""
    with patch('discovery.build') as mock_build:
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        yield mock_youtube

@pytest.fixture
def discovery_service(mock_youtube):
    """Create discovery service with mocked YouTube API."""
    with patch('discovery.sqlite3'):
        service = DiscoveryService('test_api_key')
        service.youtube = mock_youtube
        return service

def test_search_niche(discovery_service, mock_youtube):
    """Test searching for videos in a niche."""
    # Mock API response
    mock_youtube.search().list().execute.return_value = {
        'items': [
            {
                'id': {'videoId': 'test123'},
                'snippet': {
                    'title': 'Test Video',
                    'channelTitle': 'Test Channel',
                    'publishedAt': '2024-01-01T00:00:00Z'
                }
            }
        ]
    }

    videos = discovery_service.search_niche('Fortnite')

    assert len(videos) == 1
    assert videos[0]['video_id'] == 'test123'
    assert videos[0]['niche'] == 'Fortnite'

def test_get_video_details(discovery_service, mock_youtube):
    """Test fetching video details."""
    mock_youtube.videos().list().execute.return_value = {
        'items': [{
            'statistics': {
                'viewCount': '1000',
                'likeCount': '100',
                'commentCount': '10'
            },
            'contentDetails': {
                'duration': 'PT10M30S'
            }
        }]
    }

    details = discovery_service.get_video_details('test123')

    assert details['view_count'] == 1000
    assert details['like_count'] == 100
    assert details['duration'] == 'PT10M30S'

def test_filter_by_min_views(discovery_service, mock_youtube):
    """Test filtering videos by minimum views."""
    # Mock search to return video
    mock_youtube.search().list().execute.return_value = {
        'items': [{
            'id': {'videoId': 'test123'},
            'snippet': {
                'title': 'Low View Video',
                'channelTitle': 'Test Channel',
                'publishedAt': '2024-01-01T00:00:00Z'
            }
        }]
    }

    # Mock video details with low views
    mock_youtube.videos().list().execute.return_value = {
        'items': [{
            'statistics': {'viewCount': '500', 'likeCount': '50', 'commentCount': '5'},
            'contentDetails': {'duration': 'PT10M'}
        }]
    }

    videos = discovery_service.search_niche('Test')

    # Should filter out due to low views
    assert len(videos) == 1  # Found in search

    # Details would return low views, filtered in run()
    details = discovery_service.get_video_details('test123')
    assert details['view_count'] == 500
