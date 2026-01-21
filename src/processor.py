#!/usr/bin/env python3
"""
Processor Module: Main pipeline orchestrator
Coordinates all modules to process videos end-to-end.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from downloader import VideoDownloader
from transcriber import Transcriber
from analyzer import ViralMomentDetector
from editor import VideoEditor
from caption_generator import CaptionGenerator
from seo_generator import SEOGenerator
from quality_assurance import QualityAssurance
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """Process a video through the entire pipeline."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize video processor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.db = Database()

        # Initialize components
        self.downloader = VideoDownloader()
        self.transcriber = None  # Lazy load
        self.detector = None  # Lazy load
        self.editor = VideoEditor()
        self.caption_gen = CaptionGenerator(style='gaming')
        self.seo_gen = SEOGenerator()
        self.qa = QualityAssurance(strictness='strict')

    def _get_transcriber(self):
        """Lazy load transcriber."""
        if self.transcriber is None:
            try:
                self.transcriber = Transcriber(model_size='base')
            except Exception as e:
                logger.warning(f"Could not initialize transcriber: {e}")
        return self.transcriber

    def _get_detector(self):
        """Lazy load detector."""
        if self.detector is None:
            try:
                self.detector = ViralMomentDetector()
            except Exception as e:
                logger.warning(f"Could not initialize detector: {e}")
        return self.detector

    def process_video(self, video_id: str, niche: str = 'gaming') -> Dict[str, Any]:
        """
        Process a video through the complete pipeline.

        Args:
            video_id: YouTube video ID
            niche: Game niche/category

        Returns:
            Processing results
        """
        logger.info(f"=== Processing video: {video_id} ===")
        results = {
            'video_id': video_id,
            'niche': niche,
            'success': False,
            'clips_generated': [],
            'errors': []
        }

        # Step 1: Download video
        logger.info("Step 1: Downloading video...")
        video_path = self.downloader.download(video_id)
        if not video_path:
            results['errors'].append("Failed to download video")
            return results

        try:
            # Step 2: Transcribe
            logger.info("Step 2: Transcribing audio...")
            transcriber = self._get_transcriber()
            transcription = None

            if transcriber:
                transcription = transcriber.process_video(video_path)
                if not transcription:
                    logger.warning("Transcription failed, continuing without it")
                    results['errors'].append("Transcription failed")
            else:
                logger.warning("Transcriber not available, skipping")
                results['errors'].append("Transcriber not available")

            # Step 3: Detect viral moments
            logger.info("Step 3: Detecting viral moments...")
            detector = self._get_detector()
            moments = []

            if detector and transcription:
                moments = detector.analyze_transcript(transcription)
                # Select best moments
                moments = detector.select_best_moments(moments, count=3, min_score=70)

            if not moments:
                logger.error("No viral moments detected")
                results['errors'].append("No viral moments detected")
                return results

            logger.info(f"Found {len(moments)} viral moments")

            # Step 4: Generate clips
            logger.info("Step 4: Generating clips...")
            platforms = ['youtube_shorts', 'tiktok', 'instagram_reels']

            for moment in moments:
                for platform in platforms:
                    try:
                        # Extract and convert clip
                        clip_path = self.editor.process_clip_for_platform(
                            video_path,
                            moment['start'],
                            moment['end'],
                            platform
                        )

                        if clip_path:
                            # Generate metadata
                            metadata = self.seo_gen.generate_metadata(moment, niche, platform)

                            # QA check
                            qa_result = self.qa.check_clip({
                                'clip_path': clip_path,
                                'quote': moment.get('quote', ''),
                                'duration': moment['end'] - moment['start'],
                                'platform': platform
                            })

                            # Save to database
                            clip_data = {
                                'youtube_id': video_id,
                                'clip_path': clip_path,
                                'platform': platform,
                                'start_time': moment['start'],
                                'end_time': moment['end'],
                                'moment_type': moment['type'],
                                'quote': moment['quote'],
                                'virality_score': moment['virality_score'],
                                'title': metadata['title'],
                                'description': metadata['description'],
                                'hashtags': metadata['hashtags'],
                                'qa_passed': qa_result['passed']
                            }

                            clip_id = self.db.add_clip(clip_data)

                            results['clips_generated'].append({
                                'platform': platform,
                                'clip_path': clip_path,
                                'clip_id': clip_id,
                                'qa_passed': qa_result['passed'],
                                'qa_score': qa_result.get('overall_score', 0),
                                'virality_score': moment['virality_score']
                            })

                            logger.info(f"✓ Generated {platform} clip (QA: {qa_result['passed']})")

                    except Exception as e:
                        logger.error(f"Error processing moment for {platform}: {e}")
                        results['errors'].append(f"{platform}: {str(e)}")

            # Step 5: Mark video as processed
            self.db.mark_video_processed(video_id)

            results['success'] = True
            logger.info(f"=== Processing complete: {len(results['clips_generated'])} clips generated ===")

            return results

        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            results['errors'].append(f"Processing error: {str(e)}")
            return results

        finally:
            # Cleanup downloaded video
            if video_path and os.path.exists(video_path):
                self.downloader.cleanup(video_path)

def main():
    """Main entry point for video processing."""
    parser = argparse.ArgumentParser(description='Process a video for viral clips')
    parser.add_argument('--video-id', required=True, help='YouTube video ID')
    parser.add_argument('--niche', default='gaming', help='Game niche/category')
    parser.add_argument('--output', help='Output JSON file for results')

    args = parser.parse_args()

    # Load config
    from config_validator import ConfigValidator
    validator = ConfigValidator()
    config = validator.get_config() or {}

    # Process video
    processor = VideoProcessor(config)
    results = processor.process_video(args.video_id, args.niche)

    # Output results
    os.makedirs('data', exist_ok=True)

    # Save to file
    if args.output:
        output_path = args.output
    else:
        output_path = f"data/process_results_{args.video_id}.json"

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results saved to: {output_path}")

    # Print summary
    print(f"\n{'='*50}")
    print(f"Processing Summary for {args.video_id}")
    print(f"{'='*50}")
    print(f"Success: {results['success']}")
    print(f"Clips generated: {len(results['clips_generated'])}")
    print(f"Errors: {len(results['errors'])}")

    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")

    if results['clips_generated']:
        print(f"\nClips:")
        for clip in results['clips_generated']:
            status = "✓" if clip['qa_passed'] else "✗"
            print(f"  {status} {clip['platform']}: {clip['clip_path']}")
            print(f"      Virality: {clip['virality_score']}, QA: {clip['qa_score']}")

    # Exit with error if processing failed
    sys.exit(0 if results['success'] else 1)

if __name__ == '__main__':
    main()
