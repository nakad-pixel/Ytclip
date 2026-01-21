#!/usr/bin/env python3
"""
Integration Tests for AutoClip Gaming Pipeline
Tests the complete workflow from discovery to publishing.
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import Mock, patch, MagicMock

# Mock all external dependencies
@pytest.fixture
def mock_dependencies():
    """Mock all external API dependencies."""
    with patch('discovery.build'), \
         patch('downloader.subprocess'), \
         patch('transcriber.whisper'), \
         patch('analyzer.genai'), \
         patch('editor.subprocess'), \
         patch('publishers.youtube.build'), \
         patch('publishers.youtube.pickle'), \
         patch('database.sqlite3'):
        yield

def test_full_pipeline(mock_dependencies):
    """Test complete pipeline from video discovery to clip generation."""
    from processor import VideoProcessor

    # Create mock video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        video_path = f.name

    try:
        # Create processor
        processor = VideoProcessor()

        # Mock downloader to return test video
        processor.downloader.download = Mock(return_value=video_path)
        processor.downloader.cleanup = Mock()

        # Mock transcriber to return test data
        processor.transcriber = Mock()
        processor.transcriber.process_video = Mock(return_value={
            'language': 'en',
            'duration': 60.0,
            'segments': [
                {'start': 10.0, 'end': 15.0, 'text': 'This is an exciting moment', 'words': []},
                {'start': 20.0, 'end': 25.0, 'text': 'This is very funny', 'words': []}
            ]
        })

        # Mock detector to return moments
        processor.detector = Mock()
        processor.detector.analyze_transcript = Mock(return_value=[
            {
                'start': 10.0,
                'end': 15.0,
                'type': 'exciting',
                'description': 'Exciting moment',
                'quote': 'This is an exciting moment',
                'virality_score': 85
            }
        ])
        processor.detector.select_best_moments = Mock(return_value=[
            {
                'start': 10.0,
                'end': 15.0,
                'type': 'exciting',
                'description': 'Exciting moment',
                'quote': 'This is an exciting moment',
                'virality_score': 85
            }
        ])

        # Mock editor
        processor.editor.process_clip_for_platform = Mock(return_value='test_clip.mp4')

        # Mock database
        processor.db.add_clip = Mock(return_value=1)
        processor.db.mark_video_processed = Mock(return_value=True)

        # Process video
        results = processor.process_video('test_video_id', 'Fortnite')

        # Verify results
        assert results['success'] == True
        assert len(results['clips_generated']) > 0
        assert processor.downloader.download.called
        assert processor.transcriber.process_video.called
        assert processor.detector.analyze_transcript.called

    finally:
        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)

def test_config_validation():
    """Test configuration validation."""
    from config_validator import ConfigValidator
    import yaml

    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'system': {
                'name': 'Test',
                'version': '1.0.0',
                'environment': 'production'
            },
            'discovery': {
                'niches': ['Fortnite'],
                'min_views': 10000,
                'max_age_days': 7
            },
            'video_processing': {},
            'publishing': {},
            'database': {}
        }, f)
        config_path = f.name

    try:
        validator = ConfigValidator(config_path)
        is_valid, errors = validator.validate()

        # Check if environment variables are set (they won't be in tests)
        # So we expect some errors about missing env vars
        config = validator.get_config()
        assert config is not None
        assert config['system']['name'] == 'Test'

    finally:
        os.remove(config_path)

def test_database_operations():
    """Test database operations."""
    from database import Database

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db = Database(db_path)

        # Test adding video
        video_data = {
            'youtube_id': 'test123',
            'title': 'Test Video',
            'channel': 'Test Channel',
            'view_count': 1000,
            'niche': 'Fortnite',
            'url': 'https://youtube.com/watch?v=test123'
        }

        video_id = db.add_video(video_data)
        assert video_id > 0

        # Test retrieving video
        video = db.get_video('test123')
        assert video is not None
        assert video['title'] == 'Test Video'

        # Test adding clip
        clip_data = {
            'youtube_id': 'test123',
            'clip_path': 'test.mp4',
            'platform': 'youtube_shorts',
            'start_time': 10.0,
            'end_time': 15.0,
            'moment_type': 'exciting',
            'quote': 'Test quote',
            'virality_score': 85,
            'title': 'Test Clip',
            'description': 'Test Description',
            'hashtags': ['#gaming', '#viral'],
            'qa_passed': True
        }

        clip_id = db.add_clip(clip_data)
        assert clip_id > 0

        # Test state operations
        db.set_state('test_key', 'test_value')
        value = db.get_state('test_key')
        assert value == 'test_value'

    finally:
        os.remove(db_path)

def test_qa_workflow():
    """Test quality assurance workflow."""
    from quality_assurance import QualityAssurance

    qa = QualityAssurance(strictness='strict')

    # Test good clip
    good_clip = {
        'clip_path': 'test.mp4',
        'quote': 'This is an exciting moment from the game!',
        'start': 10.0,
        'end': 25.0,
        'platform': 'youtube_shorts'
    }

    report = qa.check_clip(good_clip)
    assert report['passed'] == True
    assert report['overall_score'] >= 70

    # Test bad clip (too long for YouTube)
    bad_clip = {
        'clip_path': 'test.mp4',
        'quote': 'Short',
        'start': 10.0,
        'end': 75.0,  # 65 seconds - too long for YouTube Shorts
        'platform': 'youtube_shorts'
    }

    report = qa.check_clip(bad_clip)
    assert report['passed'] == False
    assert len(report['issues']) > 0

def test_seo_generation():
    """Test SEO metadata generation."""
    from seo_generator import SEOGenerator

    seo = SEOGenerator()

    moment = {
        'start': 10.0,
        'end': 15.0,
        'type': 'exciting',
        'quote': 'I can\'t believe that happened!'
    }

    # Test YouTube
    metadata = seo.generate_metadata(moment, 'Fortnite', 'youtube_shorts')

    assert 'title' in metadata
    assert 'description' in metadata
    assert 'hashtags' in metadata
    assert len(metadata['title']) > 0
    assert len(metadata['hashtags']) > 0

    # Test TikTok
    metadata_tiktok = seo.generate_metadata(moment, 'Fortnite', 'tiktok')
    assert metadata_tiktok['platform'] == 'tiktok'

    # Test Instagram
    metadata_insta = seo.generate_metadata(moment, 'Fortnite', 'instagram_reels')
    assert metadata_insta['platform'] == 'instagram_reels'

def test_caption_generation():
    """Test caption generation."""
    from caption_generator import CaptionGenerator

    gen = CaptionGenerator(style='gaming')

    moment = {
        'start': 10.0,
        'end': 15.0,
        'type': 'exciting',
        'quote': 'I can\'t believe that happened!'
    }

    caption = gen.generate_caption(moment)

    assert 'text' in caption
    assert 'start' in caption
    assert 'end' in caption
    assert 'color' in caption
    assert len(caption['text']) > 0

    # Test word-by-word captions
    word_captions = gen.create_word_by_word_captions(moment)
    assert len(word_captions) > 0
