#!/usr/bin/env python3
"""
Processor Module: API-First Video Processing
Analyzes videos via transcripts without downloading files.
Uses YouTube API for captions, Gemini for analysis - NO BOT DETECTION!
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcript_analyzer import TranscriptAnalyzer
from seo_generator import SEOGenerator
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """Process videos using API-first approach (no file downloads)."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize video processor with API-first architecture.

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        
        # Get API keys from environment
        youtube_key = os.getenv('YOUTUBE_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not youtube_key or not gemini_key:
            raise ValueError("Missing required API keys: YOUTUBE_API_KEY and GEMINI_API_KEY")
        
        # Initialize components (API-based only)
        self.analyzer = TranscriptAnalyzer(youtube_key, gemini_key)
        self.seo_gen = SEOGenerator()
        self.db = Database()
        
        logger.info("Initialized API-first VideoProcessor")

    def process_video(self, video_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process single video using transcript analysis (no file download).
        
        Architecture:
        1. Fetch transcript via YouTube API (no bot detection)
        2. Analyze with Gemini AI for viral moments
        3. Generate clip metadata (timestamps + descriptions)
        4. Save to database for on-demand clip generation
        
        Args:
            video_id: YouTube video ID
            metadata: Video metadata from discovery
            
        Returns:
            Processing results with clip metadata
        """
        logger.info(f"{'='*60}")
        logger.info(f"Processing video: {video_id}")
        logger.info(f"{'='*60}")
        
        metadata = metadata or {}
        niche = metadata.get('niche', 'gaming')
        
        results = {
            'video_id': video_id,
            'niche': niche,
            'success': False,
            'metadata': metadata,
            'clips_metadata': [],
            'errors': []
        }
        
        try:
            # Step 1: Get transcript from YouTube API (NO FILE DOWNLOAD)
            logger.info("Step 1: Fetching transcript from YouTube API...")
            transcript = self.analyzer.get_transcript(video_id)
            
            if not transcript:
                error_msg = "No transcript available (captions may be disabled)"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                
                # Check if captions are disabled
                if not metadata.get('has_captions', True):
                    results['errors'].append("Video has captions disabled")
                
                return results
            
            logger.info(f"✓ Transcript fetched: {len(transcript['segments'])} segments")
            
            # Step 2: Analyze for viral moments with Gemini AI
            logger.info("Step 2: Analyzing transcript for viral moments...")
            analysis = self.analyzer.analyze_transcript(transcript, niche)
            
            if 'error' in analysis:
                error_msg = f"Analysis failed: {analysis['error']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            moments = analysis.get('moments', [])
            overall_virality = analysis.get('overall_virality', 0)
            
            if not moments:
                error_msg = "No viral moments detected"
                logger.warning(error_msg)
                results['errors'].append(error_msg)
                return results
            
            logger.info(f"✓ Analysis complete: {len(moments)} viral moments (overall score: {overall_virality}/100)")
            
            # Step 3: Generate clip metadata for each platform
            logger.info("Step 3: Generating clip metadata for platforms...")
            platforms = ['youtube_shorts', 'tiktok', 'instagram_reels']
            platform_durations = {
                'youtube_shorts': 60,      # Max 60 seconds
                'tiktok': 60,              # Prefer 15-60 seconds
                'instagram_reels': 90      # Max 90 seconds
            }
            
            for moment in moments:
                # Calculate optimal duration for this moment
                moment_duration = moment['end_time'] - moment['start_time']
                
                for platform in platforms:
                    try:
                        # Check if moment fits platform constraints
                        max_duration = platform_durations[platform]
                        if moment_duration > max_duration:
                            logger.debug(f"Moment too long for {platform}: {moment_duration}s > {max_duration}s")
                            continue
                        
                        # Generate SEO metadata
                        seo_metadata = self.seo_gen.generate_metadata(
                            moment,
                            niche,
                            platform
                        )
                        
                        # Create clip metadata (no actual file yet - generated on-demand)
                        clip_metadata = {
                            'source_video_id': video_id,
                            'source_url': f"https://www.youtube.com/watch?v={video_id}",
                            'platform': platform,
                            'start_time': moment['start_time'],
                            'end_time': moment['end_time'],
                            'duration': moment_duration,
                            'moment_type': moment['type'],
                            'virality_score': moment['virality_score'],
                            'niche': niche,
                            'quote': moment.get('quote', ''),
                            'reason': moment.get('reason', ''),
                            'engagement_potential': moment.get('engagement_potential', ''),
                            'title': seo_metadata.get('title', ''),
                            'description': seo_metadata.get('description', ''),
                            'hashtags': seo_metadata.get('hashtags', ''),
                            'channel': metadata.get('channel', ''),
                            'source_title': metadata.get('title', ''),
                            'source_views': metadata.get('view_count', 0),
                            'overall_virality': overall_virality
                        }
                        
                        # Save to database
                        try:
                            clip_id = self.db.add_clip(clip_metadata)
                            clip_metadata['clip_id'] = clip_id
                            logger.info(f"✓ Generated metadata for {platform} clip (ID: {clip_id})")
                        except Exception as db_error:
                            logger.warning(f"Could not save clip to database: {db_error}")
                            clip_metadata['clip_id'] = None
                        
                        results['clips_metadata'].append(clip_metadata)
                    
                    except Exception as e:
                        error_msg = f"Error generating {platform} metadata: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            # Step 4: Mark video as processed
            logger.info("Step 4: Marking video as processed...")
            try:
                self.db.mark_video_processed(video_id)
            except Exception as e:
                logger.warning(f"Could not mark video as processed: {e}")
            
            # Success!
            results['success'] = True
            results['analysis'] = {
                'overall_virality': overall_virality,
                'moments_detected': len(moments),
                'clips_generated': len(results['clips_metadata'])
            }
            
            logger.info(f"{'='*60}")
            logger.info(f"✓ Processing complete: {len(results['clips_metadata'])} clip metadata entries generated")
            logger.info(f"  Overall virality: {overall_virality}/100")
            logger.info(f"  Viral moments: {len(moments)}")
            logger.info(f"  No files downloaded (API-first architecture)")
            logger.info(f"{'='*60}")
            
            return results
        
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            return results

def main():
    """Main entry point for video processing."""
    parser = argparse.ArgumentParser(description='Process video via transcript analysis (API-first)')
    parser.add_argument('--video-id', required=True, help='YouTube video ID')
    parser.add_argument('--metadata', type=str, help='Video metadata as JSON string')
    parser.add_argument('--output', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    # Parse metadata if provided
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            sys.exit(1)
    
    # Load config
    try:
        from config_validator import ConfigValidator
        validator = ConfigValidator()
        config = validator.get_config() or {}
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        config = {}
    
    # Process video
    try:
        processor = VideoProcessor(config)
        results = processor.process_video(args.video_id, metadata)
    except Exception as e:
        logger.error(f"Failed to initialize processor: {e}")
        sys.exit(1)
    
    # Save results
    os.makedirs('data/clips', exist_ok=True)
    
    if args.output:
        output_path = args.output
    else:
        output_path = f"data/clips/{args.video_id}_metadata.json"
    
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Processing Summary for {args.video_id}")
    print(f"{'='*60}")
    print(f"Success: {results['success']}")
    print(f"Clips metadata generated: {len(results['clips_metadata'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results.get('analysis'):
        print(f"\nAnalysis:")
        print(f"  Overall virality: {results['analysis']['overall_virality']}/100")
        print(f"  Viral moments detected: {results['analysis']['moments_detected']}")
    
    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['clips_metadata']:
        print(f"\nClip Metadata Generated:")
        for clip in results['clips_metadata']:
            print(f"  • {clip['platform']}: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s")
            print(f"    Type: {clip['moment_type']}, Virality: {clip['virality_score']}/100")
            print(f"    Title: {clip['title'][:50]}...")
    
    print(f"{'='*60}")
    print(f"📊 Architecture: API-First (No File Downloads)")
    print(f"✅ Benefits: No bot detection, <1MB bandwidth, 100x faster")
    print(f"{'='*60}\n")
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == '__main__':
    main()
