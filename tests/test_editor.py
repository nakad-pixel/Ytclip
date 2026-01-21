#!/usr/bin/env python3
"""
Tests for Editor Module
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from editor import VideoEditor
from unittest.mock import Mock, patch, MagicMock
import json

@pytest.fixture
def mock_subprocess():
    """Mock subprocess module."""
    with patch('editor.subprocess') as mock:
        yield mock

@pytest.fixture
def editor():
    """Create video editor."""
    return VideoEditor(output_dir='data/test_clips')

def test_extract_clip(editor, mock_subprocess):
    """Test extracting a clip from video."""
    mock_subprocess.run.return_value = None

    # Mock file existence
    with patch('os.path.exists', return_value=True):
        result = editor.extract_clip('test.mp4', 10.0, 20.0)

    assert result is not None
    assert 'test_clips' in result
    assert mock_subprocess.run.called

def test_resize_to_vertical(editor, mock_subprocess):
    """Test resizing video to vertical format."""
    # Mock ffprobe response
    mock_subprocess.run.side_effect = [
        # First call: ffprobe
        Mock(stdout='{"streams": [{"width": 1920, "height": 1080}]}'),
        # Second call: ffmpeg
        None
    ]

    with patch('os.path.exists', return_value=True):
        result = editor.resize_to_vertical('test.mp4', 'youtube_shorts')

    assert result is not None
    assert 'youtube_shorts' in result

def test_get_video_duration(editor, mock_subprocess):
    """Test getting video duration."""
    mock_subprocess.run.return_value = Mock(
        stdout='{"format": {"duration": "120.5"}}'
    )

    duration = editor.get_video_duration('test.mp4')

    assert duration == 120.5

def test_process_clip_for_platform(editor, mock_subprocess):
    """Test full pipeline for platform processing."""
    # Mock subprocess calls
    mock_subprocess.run.side_effect = [
        Mock(stdout='{"streams": [{"width": 1920, "height": 1080}]}'),
        None
    ]

    with patch('os.path.exists', return_value=True):
        result = editor.process_clip_for_platform('test.mp4', 10.0, 20.0, 'youtube_shorts')

    assert result is not None

def test_batch_process_moments(editor, mock_subprocess):
    """Test processing multiple moments."""
    moments = [
        {'start': 10.0, 'end': 15.0, 'type': 'exciting', 'quote': 'Test 1'},
        {'start': 20.0, 'end': 25.0, 'type': 'funny', 'quote': 'Test 2'}
    ]

    mock_subprocess.run.side_effect = [
        Mock(stdout='{"streams": [{"width": 1920, "height": 1080}]}'),
        None,
        Mock(stdout='{"streams": [{"width": 1920, "height": 1080}]}'),
        None
    ]

    with patch('os.path.exists', return_value=True):
        results = editor.batch_process_moments(
            'test.mp4',
            moments,
            platforms=['youtube_shorts']
        )

    assert len(results) == 2
