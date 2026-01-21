#!/usr/bin/env python3
"""
Analyzer Module: Use Gemini AI to detect viral moments
Analyzes transcription for exciting, funny, or engaging content.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default virality scoring weights
DEFAULT_WEIGHTS = {
    'audio_excitement': 0.25,
    'visual_intensity': 0.20,
    'emotional_arc': 0.20,
    'hook_potential': 0.15,
    'trend_alignment': 0.10
}

class ViralMomentDetector:
    """Detect viral moments in gaming videos using Gemini AI."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize detector with Gemini API key."""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI package not installed")

        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not provided")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logger.info("Initialized Gemini Pro model")

    def analyze_transcript(self, transcription: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze transcription for viral moments."""
        segments = transcription.get('segments', [])

        if not segments:
            logger.warning("No segments found in transcription")
            return []

        # Group segments into chunks for analysis
        chunks = self._create_analysis_chunks(segments)

        viral_moments = []
        for chunk in chunks:
            moments = self._detect_viral_moments(chunk)
            viral_moments.extend(moments)

        # Score and rank moments
        scored_moments = [self._score_moment(m) for m in viral_moments]
        scored_moments.sort(key=lambda x: x['virality_score'], reverse=True)

        logger.info(f"Detected {len(scored_moments)} potential viral moments")
        return scored_moments

    def _create_analysis_chunks(self, segments: List[Dict], chunk_duration: int = 30) -> List[List[Dict]]:
        """Create time-based chunks of segments for analysis."""
        chunks = []
        current_chunk = []
        chunk_start = segments[0]['start'] if segments else 0
        chunk_end = chunk_start + chunk_duration

        for seg in segments:
            if seg['start'] > chunk_end:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [seg]
                chunk_start = seg['start']
                chunk_end = chunk_start + chunk_duration
            else:
                current_chunk.append(seg)

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _detect_viral_moments(self, chunk: List[Dict]) -> List[Dict[str, Any]]:
        """Use Gemini to detect viral moments in a chunk."""
        # Prepare text from chunk
        text = '\n'.join([
            f"[{seg['start']:.1f}s] {seg['text']}"
            for seg in chunk
        ])

        # Build prompt
        prompt = f"""Analyze this transcript segment from a gaming video and identify the most viral moments.

Format: Timestamp in seconds | Type (funny/exciting/shocking/emotional) | Description | Quote (exact words)
Quote must be EXACT from the transcript. Use 10-15 words maximum.

Rules:
- Select 1-3 best moments maximum per segment
- Must be under 30 seconds for short-form content
- Quote must be verbatim from the transcript below
- Timestamps must be within the provided range
- Include start and end timestamps separately

Transcript segment:
{text}

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "moments": [
    {{
      "start": <start_time_in_seconds>,
      "end": <end_time_in_seconds>,
      "type": <type>,
      "description": <description>,
      "quote": "<exact_quote_from_transcript>"
    }}
  ]
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean up markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.strip('```')
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
                elif response_text.startswith('python'):
                    response_text = response_text[7:].strip()

            # Parse JSON response
            try:
                result = json.loads(response_text)
                moments = result.get('moments', [])

                # Validate moments are within chunk bounds
                chunk_start = chunk[0]['start']
                chunk_end = chunk[-1]['end']

                valid_moments = []
                for moment in moments:
                    if (chunk_start <= moment['start'] <= chunk_end and
                        chunk_start <= moment['end'] <= chunk_end):
                        valid_moments.append(moment)
                    else:
                        logger.warning(f"Filtered out moment outside chunk bounds: {moment}")

                return valid_moments

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response: {e}")
                logger.debug(f"Response text: {response_text}")
                return []

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return []

    def _score_moment(self, moment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate virality score for a moment."""
        score = 0
        reasons = []

        # Base score from moment type
        type_scores = {
            'funny': 85,
            'exciting': 80,
            'shocking': 75,
            'emotional': 70
        }
        base_score = type_scores.get(moment.get('type', 'exciting'), 70)
        score += base_score * DEFAULT_WEIGHTS['emotional_arc']
        reasons.append(f"Type: {moment.get('type')}")

        # Quote length check (shorter = better for short-form)
        quote_length = len(moment.get('quote', '').split())
        if quote_length <= 8:
            score += 15 * DEFAULT_WEIGHTS['hook_potential']
            reasons.append("Short quote (good hook)")
        elif quote_length <= 12:
            score += 10 * DEFAULT_WEIGHTS['hook_potential']
            reasons.append("Medium quote")

        # Duration check (shorter = better for shorts)
        duration = moment['end'] - moment['start']
        if duration <= 15:
            score += 20 * DEFAULT_WEIGHTS['trend_alignment']
            reasons.append("Short duration (trending)")
        elif duration <= 25:
            score += 10 * DEFAULT_WEIGHTS['trend_alignment']
            reasons.append("Medium duration")

        moment['virality_score'] = min(100, round(score, 1))
        moment['score_reasons'] = reasons

        return moment

    def select_best_moments(self, moments: List[Dict], count: int = 3, min_score: float = 70) -> List[Dict]:
        """Select top moments by virality score."""
        filtered = [m for m in moments if m['virality_score'] >= min_score]
        return filtered[:count]

def main():
    """Test analyzer with a transcription file."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <transcription.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        transcription = json.load(f)

    detector = ViralMomentDetector()
    moments = detector.analyze_transcript(transcription)

    print(f"\nFound {len(moments)} viral moments:")
    for i, moment in enumerate(moments[:5], 1):
        print(f"\n{i}. Score: {moment['virality_score']}/100")
        print(f"   Time: {moment['start']:.1f}s - {moment['end']:.1f}s")
        print(f"   Type: {moment['type']}")
        print(f"   Quote: \"{moment['quote']}\"")
        print(f"   Reasons: {', '.join(moment['score_reasons'])}")

if __name__ == '__main__':
    main()
