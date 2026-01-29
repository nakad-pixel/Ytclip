#!/usr/bin/env python3
"""
Transcript Analyzer: Analyze video captions without downloading files
Uses YouTube API to get captions, then Gemini AI to analyze.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """Analyze video transcripts from captions."""
    
    def __init__(self, youtube_api_key: str, gemini_api_key: str):
        """
        Initialize transcript analyzer.
        
        Args:
            youtube_api_key: YouTube Data API key
            gemini_api_key: Gemini API key
        """
        if not youtube_api_key or not gemini_api_key:
            raise ValueError("Both YouTube and Gemini API keys are required")
        
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("Initialized TranscriptAnalyzer with YouTube API and Gemini AI")
    
    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video transcript from captions.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with 'text' (full transcript) and 'segments' (timestamped)
            or None if captions unavailable
        """
        try:
            logger.info(f"Fetching transcript for video: {video_id}")
            
            # Get available captions
            caption_request = self.youtube.captions().list(
                videoId=video_id,
                part='snippet'
            )
            captions_response = caption_request.execute()
            
            if not captions_response.get('items'):
                logger.warning(f"No captions available for {video_id}")
                return None
            
            # Get caption track ID (prefer English, auto-generated is fine)
            caption_id = None
            caption_lang = None
            
            # Priority order: English manual > English auto > Any manual > Any auto
            for caption in captions_response['items']:
                lang = caption['snippet']['language']
                track_kind = caption['snippet'].get('trackKind', 'standard')
                
                if lang == 'en' and track_kind == 'standard':
                    caption_id = caption['id']
                    caption_lang = lang
                    break
                elif lang == 'en' and track_kind == 'asr':
                    caption_id = caption['id']
                    caption_lang = lang
                    # Continue searching for manual captions
            
            # If no English found, use first available
            if not caption_id:
                caption_id = captions_response['items'][0]['id']
                caption_lang = captions_response['items'][0]['snippet']['language']
            
            logger.info(f"Using caption track: {caption_id} (language: {caption_lang})")
            
            # Download caption track in SRT format (easier to parse)
            download_request = self.youtube.captions().download(
                id=caption_id,
                tfmt='srt'
            )
            transcript_data = download_request.execute()
            
            # Parse SRT format
            parsed = self._parse_srt(transcript_data)
            
            logger.info(f"Successfully fetched transcript: {len(parsed['segments'])} segments")
            return parsed
        
        except HttpError as e:
            if e.resp.status == 403:
                logger.error(f"Permission denied for captions: {video_id}. Caption download may be restricted.")
            else:
                logger.error(f"HTTP error getting transcript for {video_id}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {e}")
            return None
    
    def _parse_srt(self, srt_data: str) -> Dict[str, Any]:
        """
        Parse SRT subtitle format into structured data.
        
        Args:
            srt_data: Raw SRT format string
            
        Returns:
            Dictionary with 'text' and 'segments'
        """
        segments = []
        full_text = []
        
        # SRT format: index, timestamp, text, blank line
        # Example:
        # 1
        # 00:00:00,000 --> 00:00:02,500
        # Hello world
        
        entries = srt_data.strip().split('\n\n')
        
        for entry in entries:
            lines = entry.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # Line 0: index (ignore)
                # Line 1: timestamp
                timestamp_line = lines[1]
                start_str, end_str = timestamp_line.split(' --> ')
                
                start_time = self._srt_time_to_seconds(start_str)
                end_time = self._srt_time_to_seconds(end_str)
                
                # Line 2+: text (may be multi-line)
                text = ' '.join(lines[2:])
                
                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'text': text.strip()
                })
                
                full_text.append(text.strip())
            
            except Exception as e:
                logger.debug(f"Failed to parse SRT entry: {e}")
                continue
        
        return {
            'text': ' '.join(full_text),
            'segments': segments
        }
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """
        Convert SRT timestamp to seconds.
        
        Args:
            time_str: Time string like "00:01:23,456"
            
        Returns:
            Time in seconds (float)
        """
        # Format: HH:MM:SS,mmm
        time_str = time_str.strip()
        match = re.match(r'(\d+):(\d+):(\d+)[,\.](\d+)', time_str)
        
        if not match:
            return 0.0
        
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4))
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        return total_seconds
    
    def analyze_transcript(self, transcript: Dict[str, Any], niche: str) -> Dict[str, Any]:
        """
        Analyze transcript for viral moments using Gemini.
        
        Args:
            transcript: Transcript dictionary with 'text' and 'segments'
            niche: Game niche/category
            
        Returns:
            Analysis results with moments array and overall virality score
        """
        if not transcript or not transcript.get('segments'):
            return {'error': 'No transcript available'}
        
        try:
            # Build timestamped transcript for prompt
            timestamped_text = '\n'.join([
                f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}"
                for seg in transcript['segments']
            ])
            
            prompt = f"""Analyze this {niche} gaming video transcript and identify viral moments suitable for short-form content (YouTube Shorts, TikTok, Instagram Reels).

Transcript with timestamps:
{timestamped_text}

For each viral moment, provide:
1. **start_time**: Start timestamp in seconds (must match a timestamp from the transcript)
2. **end_time**: End timestamp in seconds (must be within 15-60 seconds from start)
3. **type**: One of: exciting, funny, shocking, emotional, epic
4. **virality_score**: Score from 0-100 based on engagement potential
5. **reason**: Why this moment is viral (be specific about what makes it engaging)
6. **engagement_potential**: Expected engagement type (comments, shares, likes, views)
7. **quote**: Exact quote from the transcript (10-15 words max for hook potential)

Requirements:
- Identify 3-6 best moments maximum
- Each clip must be 15-60 seconds (optimal for short-form)
- Prioritize moments with high energy, surprises, or emotional peaks
- Quote must be verbatim from transcript
- Consider what would make someone stop scrolling

Also provide:
- **overall_virality**: Overall video virality score (0-100)

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "overall_virality": <score>,
  "moments": [
    {{
      "start_time": <seconds>,
      "end_time": <seconds>,
      "type": "<type>",
      "virality_score": <score>,
      "reason": "<explanation>",
      "engagement_potential": "<type>",
      "quote": "<exact_quote>"
    }}
  ]
}}"""
            
            logger.info(f"Analyzing transcript with Gemini AI (niche: {niche})...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.strip('```')
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Validate response structure
            if 'moments' not in result:
                logger.error("Invalid response: missing 'moments' field")
                return {'error': 'Invalid AI response format'}
            
            # Validate and filter moments
            valid_moments = []
            for moment in result.get('moments', []):
                # Check required fields
                required_fields = ['start_time', 'end_time', 'type', 'virality_score']
                if not all(field in moment for field in required_fields):
                    logger.warning(f"Skipping moment with missing fields: {moment}")
                    continue
                
                # Validate duration (15-60 seconds)
                duration = moment['end_time'] - moment['start_time']
                if duration < 15 or duration > 60:
                    logger.warning(f"Skipping moment with invalid duration: {duration}s")
                    continue
                
                # Validate timestamps are within transcript range
                max_time = max(seg['end'] for seg in transcript['segments'])
                if moment['start_time'] < 0 or moment['end_time'] > max_time:
                    logger.warning(f"Skipping moment with out-of-range timestamps")
                    continue
                
                valid_moments.append(moment)
            
            result['moments'] = valid_moments
            
            logger.info(f"Analysis complete: {len(valid_moments)} valid moments identified")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return {'error': 'Failed to parse AI response'}
        
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}", exc_info=True)
            return {'error': str(e)}
    
    def get_video_duration(self, video_id: str) -> Optional[float]:
        """
        Get video duration in seconds.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Duration in seconds or None
        """
        try:
            request = self.youtube.videos().list(
                id=video_id,
                part='contentDetails'
            )
            response = request.execute()
            
            if response.get('items'):
                duration_str = response['items'][0]['contentDetails']['duration']
                # Parse ISO 8601 duration (e.g., "PT5M30S")
                duration = self._parse_iso8601_duration(duration_str)
                return duration
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return None
    
    def _parse_iso8601_duration(self, duration_str: str) -> float:
        """
        Parse ISO 8601 duration format.
        
        Args:
            duration_str: Duration string like "PT5M30S"
            
        Returns:
            Duration in seconds
        """
        # Remove 'PT' prefix
        duration_str = duration_str.replace('PT', '')
        
        hours = 0
        minutes = 0
        seconds = 0
        
        # Parse hours
        if 'H' in duration_str:
            hours = int(duration_str.split('H')[0])
            duration_str = duration_str.split('H')[1]
        
        # Parse minutes
        if 'M' in duration_str:
            minutes = int(duration_str.split('M')[0])
            duration_str = duration_str.split('M')[1]
        
        # Parse seconds
        if 'S' in duration_str:
            seconds = int(duration_str.split('S')[0])
        
        return hours * 3600 + minutes * 60 + seconds
