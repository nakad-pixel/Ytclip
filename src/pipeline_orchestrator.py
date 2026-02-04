#!/usr/bin/env python3
"""
Pipeline Orchestrator: Manages two-phase video processing pipeline
Coordinates analysis and creation phases for optimal resource usage.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from processor import VideoProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Manages two-phase video processing pipeline."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db = Database()
        self.processor = VideoProcessor(config)

        # Get processing config
        processing_config = config.get('processing', {})
        self.max_videos_to_analyze = processing_config.get('max_videos_to_analyze', 100)
        self.virality_threshold = processing_config.get('virality_threshold', 70)
        self.max_videos_to_process = processing_config.get('max_videos_to_process', 2)

        logger.info(f"Orchestrator initialized - Analyze: {self.max_videos_to_analyze}, "
                   f"Threshold: {self.virality_threshold}, Process: {self.max_videos_to_process}")

    def run_phase_1_analysis(self) -> Dict[str, Any]:
        """
        Phase 1: Analyze all discovered videos without downloading.

        Returns:
            Results summary
        """
        logger.info("="*60)
        logger.info("PHASE 1: ANALYSIS - Analyzing discovered videos")
        logger.info("="*60)

        results = {
            'phase': 'analysis',
            'videos_analyzed': 0,
            'videos_above_threshold': 0,
            'failures': 0,
            'scores': []
        }

        # Get discovered videos
        discovered_videos = self.db.get_discovered_videos(limit=self.max_videos_to_analyze)

        if not discovered_videos:
            logger.info("No discovered videos to analyze")
            return results

        logger.info(f"Found {len(discovered_videos)} videos to analyze")

        # Analyze each video
        for idx, video in enumerate(discovered_videos, 1):
            video_id = video['youtube_id']
            niche = video.get('niche', 'gaming')

            logger.info(f"\n[{idx}/{len(discovered_videos)}] Analyzing video: {video_id}")
            logger.info(f"  Title: {video.get('title', 'Unknown')}")
            logger.info(f"  Channel: {video.get('channel', 'Unknown')}")

            try:
                # Process video in analysis mode (no download)
                result = self.processor.process_video(
                    video_id=video_id,
                    niche=niche,
                    phase='analysis'
                )

                if result.get('success'):
                    virality_score = result.get('virality_score', 0.0)
                    
                    # Update database with analysis results
                    self.db.update_video_status(
                        youtube_id=video_id,
                        status='analyzed',
                        virality_score=virality_score
                    )

                    results['videos_analyzed'] += 1
                    results['scores'].append({
                        'video_id': video_id,
                        'score': virality_score,
                        'title': video.get('title', '')
                    })

                    if virality_score >= self.virality_threshold:
                        results['videos_above_threshold'] += 1
                        logger.info(f"  ✓ Virality score: {virality_score:.1f} (ABOVE THRESHOLD)")
                    else:
                        logger.info(f"  ✓ Virality score: {virality_score:.1f} (below threshold)")
                else:
                    logger.warning(f"  ✗ Analysis failed: {result.get('errors', [])}")
                    self.db.update_video_status(video_id, 'failed')
                    results['failures'] += 1

            except Exception as e:
                logger.error(f"  ✗ Error analyzing video {video_id}: {e}")
                self.db.update_video_status(video_id, 'failed')
                results['failures'] += 1

        # Sort scores by virality
        results['scores'].sort(key=lambda x: x['score'], reverse=True)

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("PHASE 1 COMPLETE: Analysis Summary")
        logger.info("="*60)
        logger.info(f"Videos analyzed: {results['videos_analyzed']}")
        logger.info(f"Videos above threshold ({self.virality_threshold}): {results['videos_above_threshold']}")
        logger.info(f"Failures: {results['failures']}")

        if results['scores']:
            logger.info("\nTop 5 videos by virality score:")
            for i, score_data in enumerate(results['scores'][:5], 1):
                logger.info(f"  {i}. {score_data['video_id']} - {score_data['score']:.1f} - {score_data['title'][:50]}")

        return results

    def run_phase_2_creation(self) -> Dict[str, Any]:
        """
        Phase 2: Download and process top-scoring videos.

        Returns:
            Results summary
        """
        logger.info("="*60)
        logger.info("PHASE 2: CREATION - Processing top videos")
        logger.info("="*60)

        results = {
            'phase': 'creation',
            'videos_processed': 0,
            'clips_generated': 0,
            'failures': 0,
            'published_videos': []
        }

        # Get top analyzed videos
        top_videos = self.db.get_top_analyzed_videos(
            limit=self.max_videos_to_process,
            threshold=self.virality_threshold
        )

        if not top_videos:
            logger.info(f"No analyzed videos above threshold ({self.virality_threshold}) to process")
            return results

        logger.info(f"Found {len(top_videos)} videos to process")

        # Process each video
        for idx, video in enumerate(top_videos, 1):
            video_id = video['youtube_id']
            niche = video.get('niche', 'gaming')
            virality_score = video.get('virality_score', 0.0)

            logger.info(f"\n[{idx}/{len(top_videos)}] Processing video: {video_id}")
            logger.info(f"  Title: {video.get('title', 'Unknown')}")
            logger.info(f"  Virality Score: {virality_score:.1f}")

            try:
                # Mark as processing
                self.db.update_video_status(video_id, 'processing')

                # Process video in creation mode (full pipeline with download)
                result = self.processor.process_video(
                    video_id=video_id,
                    niche=niche,
                    phase='creation'
                )

                if result.get('success'):
                    clips_count = len(result.get('clips_generated', []))
                    
                    # Update database - mark as published
                    self.db.update_video_status(video_id, 'published')

                    results['videos_processed'] += 1
                    results['clips_generated'] += clips_count
                    results['published_videos'].append({
                        'video_id': video_id,
                        'clips_count': clips_count,
                        'virality_score': virality_score
                    })

                    logger.info(f"  ✓ Generated {clips_count} clips")
                else:
                    logger.warning(f"  ✗ Processing failed: {result.get('errors', [])}")
                    self.db.update_video_status(video_id, 'failed')
                    results['failures'] += 1

            except Exception as e:
                logger.error(f"  ✗ Error processing video {video_id}: {e}")
                self.db.update_video_status(video_id, 'failed')
                results['failures'] += 1

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("PHASE 2 COMPLETE: Creation Summary")
        logger.info("="*60)
        logger.info(f"Videos processed: {results['videos_processed']}")
        logger.info(f"Total clips generated: {results['clips_generated']}")
        logger.info(f"Failures: {results['failures']}")

        if results['published_videos']:
            logger.info("\nPublished videos:")
            for pub in results['published_videos']:
                logger.info(f"  • {pub['video_id']} - {pub['clips_count']} clips (score: {pub['virality_score']:.1f})")

        return results

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete pipeline: Analysis → Creation.

        This method coordinates both phases to ensure they run sequentially
        and pass data properly between them.

        Returns:
            Combined results from both phases
        """
        logger.info("="*60)
        logger.info("RUNNING FULL PIPELINE")
        logger.info("="*60)

        # Run Phase 1: Analysis
        phase1_results = self.run_phase_1_analysis()

        # Check if we have videos above threshold
        if phase1_results['videos_above_threshold'] == 0:
            logger.warning("No videos above virality threshold. Skipping Phase 2.")
            return {
                'phase1': phase1_results,
                'phase2': None,
                'total_clips': 0
            }

        # Run Phase 2: Creation
        phase2_results = self.run_phase_2_creation()

        # Combine results
        combined_results = {
            'phase1': phase1_results,
            'phase2': phase2_results,
            'total_clips': phase2_results.get('clips_generated', 0)
        }

        # Print final summary
        logger.info("\n" + "="*60)
        logger.info("FULL PIPELINE COMPLETE - Final Summary")
        logger.info("="*60)
        logger.info(f"Phase 1 - Analyzed: {phase1_results['videos_analyzed']} videos")
        logger.info(f"Phase 1 - Above threshold: {phase1_results['videos_above_threshold']} videos")
        logger.info(f"Phase 2 - Processed: {phase2_results['videos_processed']} videos")
        logger.info(f"Phase 2 - Clips generated: {phase2_results['clips_generated']} clips")
        logger.info(f"Phase 2 - Failures: {phase2_results['failures']}")

        return combined_results


def main():
    """Test orchestrator."""
    from config_validator import ConfigValidator

    validator = ConfigValidator()
    config = validator.get_config() or {}

    orchestrator = PipelineOrchestrator(config)

    # Run full pipeline
    logger.info("Running full pipeline test...")
    results = orchestrator.run_full_pipeline()
    logger.info(f"Full pipeline results: {results}")


if __name__ == '__main__':
    main()
