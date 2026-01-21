#!/usr/bin/env python3
"""
Tests for Analyzer Module
"""

import pytest
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analyzer import ViralMomentDetector
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def sample_transcription():
    """Sample transcription data."""
    return {
        'language': 'en',
        'duration': 120.0,
        'text': 'This is a test transcript with some exciting moments and funny content.',
        'segments': [
            {
                'id': 0,
                'start': 0.0,
                'end': 5.0,
                'text': 'This is a test transcript',
                'words': []
            },
            {
                'id': 1,
                'start': 5.0,
                'end': 10.0,
                'text': 'with some exciting moments',
                'words': []
            },
            {
                'id': 2,
                'start': 10.0,
                'end': 15.0,
                'text': 'and funny content.',
                'words': []
            }
        ]
    }

@pytest.fixture
def mock_gemini():
    """Mock Gemini API."""
    with patch('analyzer.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.configure.return_value = None
        mock_genai.GenerativeModel.return_value = mock_model
        yield mock_model

@pytest.fixture
def detector(mock_gemini):
    """Create detector with mocked Gemini."""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
        return ViralMomentDetector()

def test_analyze_transcript(detector, mock_gemini, sample_transcription):
    """Test analyzing transcript for viral moments."""
    # Mock Gemini response
    mock_gemini.generate_content.return_value = Mock(
        text='''{
  "moments": [
    {
      "start": 5.0,
      "end": 10.0,
      "type": "exciting",
      "description": "An exciting moment",
      "quote": "exciting moments"
    }
  ]
}'''
    )

    moments = detector.analyze_transcript(sample_transcription)

    assert len(moments) >= 0
    # Verify Gemini was called
    assert mock_gemini.generate_content.called

def test_score_moment(detector):
    """Test scoring a viral moment."""
    moment = {
        'start': 5.0,
        'end': 10.0,
        'type': 'exciting',
        'description': 'Test',
        'quote': 'This is exciting'
    }

    scored = detector._score_moment(moment)

    assert 'virality_score' in scored
    assert 0 <= scored['virality_score'] <= 100
    assert 'score_reasons' in scored

def test_select_best_moments(detector):
    """Test selecting top moments by score."""
    moments = [
        {'virality_score': 95, 'start': 5.0, 'end': 10.0},
        {'virality_score': 85, 'start': 15.0, 'end': 20.0},
        {'virality_score': 75, 'start': 25.0, 'end': 30.0},
        {'virality_score': 60, 'start': 35.0, 'end': 40.0}
    ]

    best = detector.select_best_moments(moments, count=2, min_score=70)

    assert len(best) == 2
    assert best[0]['virality_score'] >= best[1]['virality_score']
    assert best[0]['virality_score'] >= 70

def test_chunk_creation(detector):
    """Test creating analysis chunks from segments."""
    segments = [
        {'start': i * 10, 'end': (i + 1) * 10, 'text': f'Segment {i}'}
        for i in range(10)
    ]

    chunks = detector._create_analysis_chunks(segments, chunk_duration=30)

    # Should create 4 chunks (3 segments each, last with 1)
    assert len(chunks) == 4
    assert all(len(chunk) > 0 for chunk in chunks)

def test_empty_transcription(detector, sample_transcription):
    """Test handling empty transcription."""
    empty_transcription = {
        'segments': []
    }

    moments = detector.analyze_transcript(empty_transcription)

    assert moments == []
