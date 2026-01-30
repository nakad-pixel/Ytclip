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

    def process_video(self, video_id: str, niche: str = 'gaming', phase: str = 'creation') -> Dict[str, Any]:
        """
        Process a video through the pipeline.

        Args:
            video_id: YouTube video ID
            niche: Game niche/category
            phase: 'analysis' for transcript+analyze only, 'creation' for full pipeline

        Returns:
            Processing results
        """
        if phase == 'analysis':
            return self._process_analysis_phase(video_id, niche)
        else:
            return self._process_creation_phase(video_id, niche)

    def _process_analysis_phase(self, video_id: str, niche: str = 'gaming') -> Dict[str, Any]:
        """
        Phase 1: Analyze video without downloading (transcript + AI analysis only).

        Args:
            video_id: YouTube video ID
            niche: Game niche/category

        Returns:
            Analysis results with virality score
        """
        logger.info(f"=== ANALYSIS PHASE: {video_id} ===")
        results = {
            'video_id': video_id,
            'niche': niche,
            'phase': 'analysis',
            'success': False,
            'virality_score': 0.0,
            'moments_found': 0,
            'errors': []
        }

        try:
            # Use YouTube API to get transcript without downloading
            from youtube_transcript_api import YouTubeTranscriptApi
            
            logger.info("Step 1: Fetching transcript from YouTube API...")
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Convert to Whisper-like format for compatibility
                transcription = {
                    'text': ' '.join([entry['text'] for entry in transcript_list]),
                    'segments': [
                        {
                            'start': entry['start'],
                            'end': entry['start'] + entry['duration'],
                            'text': entry['text']
                        }
                        for entry in transcript_list
                    ]
                }
                
                logger.info(f"✓ Fetched transcript: {len(transcription['segments'])} segments")
            except Exception as e:
                logger.warning(f"Could not fetch transcript via API: {e}")
                results['errors'].append(f"Transcript fetch failed: {str(e)}")
                return results

            # Step 2: Detect viral moments using AI
            logger.info("Step 2: Analyzing transcript for viral moments...")
            detector = self._get_detector()
            moments = []

            if detector and transcription:
                moments = detector.analyze_transcript(transcription)
                # Select best moments
                best_moments = detector.select_best_moments(moments, count=3, min_score=70)
                
                if best_moments:
                    # Calculate average virality score
                    avg_score = sum(m['virality_score'] for m in best_moments) / len(best_moments)
                    results['virality_score'] = avg_score
                    results['moments_found'] = len(best_moments)
                    results['success'] = True
                    
                    logger.info(f"✓ Found {len(best_moments)} viral moments")
                    logger.info(f"✓ Average virality score: {avg_score:.1f}")
                else:
                    logger.warning("No viral moments above threshold")
                    results['errors'].append("No viral moments detected")
            else:
                logger.error("Detector not available or no transcription")
                results['errors'].append("Analysis failed - detector unavailable")

            return results

        except Exception as e:
            logger.error(f"Error in analysis phase: {e}", exc_info=True)
            results['errors'].append(f"Analysis error: {str(e)}")
            return results

    def _process_creation_phase(self, video_id: str, niche: str = 'gaming') -> Dict[str, Any]:
        """
        Phase 2: Full pipeline with download and clip creation.

        Args:
            video_id: YouTube video ID
            niche: Game niche/category

        Returns:
            Processing results
        """
        logger.info(f"=== CREATION PHASE: {video_id} ===")
        results = {
            'video_id': video_id,
            'niche': niche,
            'phase': 'creation',
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
    parser = argparse.ArgumentParser(description='Process videos through two-phase pipeline')
    parser.add_argument('--phase', choices=['analysis', 'creation'], 
                       help='Pipeline phase to run (analysis or creation)')
    parser.add_argument('--video-id', help='YouTube video ID (for single video mode)')
    parser.add_argument('--niche', default='gaming', help='Game niche/category')
    parser.add_argument('--output', help='Output JSON file for results')

    args = parser.parse_args()

    # Load config
    from config_validator import ConfigValidator
    validator = ConfigValidator()
    config = validator.get_config() or {}

    # Determine mode
    if args.phase:
        # Phase-based orchestration mode
        from pipeline_orchestrator import PipelineOrchestrator
        
        orchestrator = PipelineOrchestrator(config)
        
        if args.phase == 'analysis':
            logger.info("Running Phase 1: Analysis")
            results = orchestrator.run_phase_1_analysis()
        else:  # creation
            logger.info("Running Phase 2: Creation")
            results = orchestrator.run_phase_2_creation()
        
        # Save results
        os.makedirs('data', exist_ok=True)
        output_path = args.output or f"data/phase_{args.phase}_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_path}")
        
        # Exit with success if any videos were processed
        success = results.get('videos_analyzed', 0) > 0 or results.get('videos_processed', 0) > 0
        sys.exit(0 if success else 1)
    
    elif args.video_id:
        # Single video mode (legacy support)
        processor = VideoProcessor(config)
        results = processor.process_video(args.video_id, args.niche, phase='creation')
        
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
        print(f"Clips generated: {len(results.get('clips_generated', []))}")
        print(f"Errors: {len(results.get('errors', []))}")

        if results.get('errors'):
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")

        if results.get('clips_generated'):
            print(f"\nClips:")
            for clip in results['clips_generated']:
                status = "✓" if clip.get('qa_passed') else "✗"
                print(f"  {status} {clip['platform']}: {clip['clip_path']}")
                print(f"      Virality: {clip.get('virality_score', 0)}, QA: {clip.get('qa_score', 0)}")

        # Exit with error if processing failed
        sys.exit(0 if results.get('success') else 1)
    
    else:
        parser.error("Either --phase or --video-id must be specified")

if __name__ == '__main__':
    main()
