#!/usr/bin/env python3
"""
Smart Publisher: Intelligent 1-video publishing strategy
Selects and publishes only the highest earning potential clip per run.
"""

import os
import sys
import json
import logging
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from earning_calculator import EarningCalculator
from publishers.youtube import YouTubePublisher
from publishers.tiktok import TikTokPublisher
from publishers.instagram import InstagramPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartPublisher:
    """Intelligent publisher that selects best earning potential video."""

    def __init__(self, state_file: str = 'data/publishing_state.json'):
        """
        Initialize smart publisher.

        Args:
            state_file: Path to state tracking file
        """
        self.state_file = state_file
        self.earning_calculator = EarningCalculator()
        self.state = self._load_state()
        
        # Initialize platform publishers
        self.publishers = self._initialize_publishers()
        
        logger.info("Initialized SmartPublisher")

    def _initialize_publishers(self) -> Dict[str, Any]:
        """Initialize platform publishers."""
        publishers = {}
        
        try:
            publishers['youtube'] = YouTubePublisher()
            logger.info("✓ YouTube publisher initialized")
        except Exception as e:
            logger.warning(f"Could not initialize YouTube publisher: {e}")
        
        try:
            publishers['tiktok'] = TikTokPublisher()
            logger.info("✓ TikTok publisher initialized")
        except Exception as e:
            logger.warning(f"Could not initialize TikTok publisher: {e}")
        
        try:
            publishers['instagram'] = InstagramPublisher()
            logger.info("✓ Instagram publisher initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Instagram publisher: {e}")
        
        return publishers

    def _load_state(self) -> Dict[str, Any]:
        """Load publishing state to avoid duplicate uploads."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"Loaded state: {len(state.get('published_videos', []))} previously published")
                return state
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
        
        # Default state
        return {
            'published_videos': [],
            'publishing_history': [],
            'total_published': 0,
            'last_published': None,
            'daily_count': {},
            'last_updated': datetime.now().isoformat()
        }

    def _save_state(self):
        """Save current publishing state."""
        self.state['last_updated'] = datetime.now().isoformat()
        
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info("✓ State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_clip_data(self, clips_dir: str = 'data/clips') -> List[Dict[str, Any]]:
        """Load all available clip data from processing results."""
        if not os.path.exists(clips_dir):
            logger.warning(f"Clips directory {clips_dir} not found")
            return []
        
        clips = []
        
        # Look for processing result files
        result_files = glob.glob(os.path.join(clips_dir, '*_result.json'))
        
        if not result_files:
            logger.warning("No processing result files found")
            return []
        
        for result_file in result_files:
            try:
                with open(result_file, 'r') as f:
                    result_data = json.load(f)
                
                # Extract clip information
                video_clips = self._extract_clips_from_result(result_data)
                clips.extend(video_clips)
                
                logger.debug(f"Loaded {len(video_clips)} clips from {result_file}")
                
            except Exception as e:
                logger.error(f"Error loading {result_file}: {e}")
        
        logger.info(f"Loaded {len(clips)} total clips for evaluation")
        return clips

    def _extract_clips_from_result(self, result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract clip data from processor result."""
        clips = []
        
        if not result_data.get('success') or not result_data.get('clips_generated'):
            return clips
        
        video_id = result_data.get('video_id', 'unknown')
        niche = result_data.get('niche', 'gaming')
        
        for clip_info in result_data['clips_generated']:
            # Skip clips that didn't pass QA
            if not clip_info.get('qa_passed', False):
                logger.debug(f"Skipping clip {clip_info.get('clip_id')} - failed QA")
                continue
            
            clip_data = {
                'clip_id': clip_info.get('clip_id', f"{video_id}_{clip_info['platform']}"),
                'youtube_id': video_id,
                'niche': niche,
                'platform': clip_info['platform'],
                'clip_path': clip_info['clip_path'],
                'virality_score': clip_info.get('virality_score', 0),
                'start_time': clip_info.get('start_time', 0),
                'end_time': clip_info.get('end_time', 0),
                'title': clip_info.get('title', ''),
                'description': clip_info.get('description', ''),
                'hashtags': clip_info.get('hashtags', []),
                'moment_type': clip_info.get('moment_type', ''),
                'quote': clip_info.get('quote', ''),
                
                # Additional data for earning calculation
                'engagement_metrics': {
                    'excitement_level': min(100, clip_info.get('virality_score', 50) + 10),
                    'emotional_arc': min(100, clip_info.get('virality_score', 50) + 5),
                    'hook_strength': min(100, clip_info.get('virality_score', 50) + 15)
                },
                
                # Brand safety (assume safe unless data suggests otherwise)
                'brand_safety': self._assess_brand_safety(clip_info),
                
                # Processing timestamp
                'processed_at': datetime.now().isoformat()
            }
            
            clips.append(clip_data)
        
        return clips

    def _assess_brand_safety(self, clip_info: Dict[str, Any]) -> Dict[str, bool]:
        """Assess brand safety of clip based on available data."""
        # Basic brand safety assessment
        safety = {}
        
        # Check for potential profanity in quotes
        quote = clip_info.get('quote', '').lower()
        profanity_words = ['damn', 'hell', 'shit', 'fuck', 'ass', 'bitch']
        safety['profanity'] = any(word in quote for word in profanity_words)
        
        # Check moment type for violence
        moment_type = clip_info.get('moment_type', '').lower()
        safety['violence'] = any(word in moment_type for word in ['kill', 'death', 'murder', 'violence'])
        
        # Check for controversy (placeholder - would need more sophisticated analysis)
        safety['controversy'] = False
        
        # Copyright check (assume safe for now)
        safety['copyright'] = False
        
        # Explicit content check
        safety['explicit'] = any(word in moment_type for word in ['sex', 'nude', 'explicit'])
        
        return safety

    def _is_already_published(self, clip_data: Dict[str, Any]) -> bool:
        """Check if clip or video is already published."""
        clip_id = clip_data.get('clip_id')
        youtube_id = clip_data.get('youtube_id')
        
        published_videos = self.state.get('published_videos', [])
        
        # Check by clip_id
        if clip_id in [p.get('clip_id') for p in published_videos]:
            return True
        
        # Check by youtube_id (to avoid republishing same video)
        if youtube_id in [p.get('youtube_id') for p in published_videos]:
            return True
        
        return False

    def _apply_filters(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply quality and safety filters to clips."""
        logger.info("Applying filters to clips...")
        
        filtered_clips = []
        
        for clip in clips:
            # Calculate earning potential for this clip
            earning_analysis = self.earning_calculator.calculate_earning_potential(clip)
            
            # Filter 1: Minimum virality score
            if earning_analysis['virality_score'] < 70:
                logger.debug(f"Filtered out clip {clip['clip_id']}: low virality ({earning_analysis['virality_score']:.1f})")
                continue
            
            # Filter 2: Brand safety
            if earning_analysis['safety_score'] < 70:
                logger.debug(f"Filtered out clip {clip['clip_id']}: low safety score ({earning_analysis['safety_score']:.1f})")
                continue
            
            # Filter 3: Not already published
            if self._is_already_published(clip):
                logger.debug(f"Filtered out clip {clip['clip_id']}: already published")
                continue
            
            # Filter 4: Has valid file path
            if not os.path.exists(clip['clip_path']):
                logger.warning(f"Clip file not found: {clip['clip_path']}")
                continue
            
            # Add earning analysis to clip data
            clip['earning_analysis'] = earning_analysis
            filtered_clips.append(clip)
        
        logger.info(f"Filtered {len(clips)} clips down to {len(filtered_clips)} clips")
        return filtered_clips

    def _select_best_clip(self, clips: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select the best clip based on earning potential."""
        if not clips:
            logger.warning("No clips available for selection")
            return None
        
        logger.info(f"Selecting best clip from {len(clips)} candidates...")
        
        # Score all clips by earning potential
        scored_clips = []
        
        for clip in clips:
            earning_analysis = clip.get('earning_analysis')
            if not earning_analysis:
                earning_analysis = self.earning_calculator.calculate_earning_potential(clip)
            
            score = earning_analysis['final_earning_score']
            scored_clips.append((clip, score))
        
        # Sort by earning score (highest first)
        scored_clips.sort(key=lambda x: x[1], reverse=True)
        
        best_clip, best_score = scored_clips[0]
        
        logger.info(f"✓ SELECTED: {best_clip['clip_id']}")
        logger.info(f"  Earning Score: {best_score:.1f}/100")
        logger.info(f"  Expected Revenue: ${best_clip['earning_analysis']['estimated_revenue']:.2f}")
        logger.info(f"  Expected Views: {best_clip['earning_analysis']['expected_views']:,}")
        logger.info(f"  Niche: {best_clip['niche']} (CPM: ${best_clip['earning_analysis']['base_cpm']:.1f})")
        
        return best_clip

    def _publish_to_platforms(self, clip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish selected clip to all platforms."""
        logger.info("Publishing to platforms...")
        
        results = {
            'platforms': {},
            'success_count': 0,
            'total_count': 0,
            'published_clip': clip_data['clip_id']
        }
        
        # Prepare metadata for publishing
        platform_metadata = {
            'title': clip_data.get('title', f"Viral Gaming Moment - {clip_data['niche']}"),
            'description': clip_data.get('description', f"Amazing {clip_data['niche']} moment!"),
            'hashtags': clip_data.get('hashtags', []),
            'niche': clip_data['niche'],
            'moment_type': clip_data['moment_type'],
            'virality_score': clip_data.get('virality_score', 0)
        }
        
        for platform_name, publisher in self.publishers.items():
            try:
                logger.info(f"Publishing to {platform_name}...")
                
                # Prepare clip data for platform
                clip_for_platform = {
                    'clip_path': clip_data['clip_path'],
                    'metadata': platform_metadata,
                    'moment': {
                        'start': clip_data.get('start_time', 0),
                        'end': clip_data.get('end_time', 0),
                        'type': clip_data.get('moment_type', ''),
                        'quote': clip_data.get('quote', '')
                    }
                }
                
                # Publish to platform
                result = publisher.publish_clip(clip_for_platform)
                
                if result and result.get('status') == 'published':
                    results['platforms'][platform_name] = result
                    results['success_count'] += 1
                    logger.info(f"✓ Successfully published to {platform_name}")
                else:
                    results['platforms'][platform_name] = result or {'status': 'failed'}
                    logger.warning(f"✗ Failed to publish to {platform_name}")
                
                results['total_count'] += 1
                
                # Add delay between platforms to avoid rate limits
                if platform_name != list(self.publishers.keys())[-1]:
                    logger.info("Waiting 30 seconds between platforms...")
                    time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error publishing to {platform_name}: {e}")
                results['platforms'][platform_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['total_count'] += 1
        
        return results

    def _update_state(self, clip_data: Dict[str, Any], publish_results: Dict[str, Any]):
        """Update state after successful publishing."""
        # Add to published videos
        published_entry = {
            'clip_id': clip_data['clip_id'],
            'youtube_id': clip_data['youtube_id'],
            'platform': clip_data['platform'],
            'published_at': datetime.now().isoformat(),
            'virality_score': clip_data.get('virality_score', 0),
            'earning_score': clip_data['earning_analysis']['final_earning_score'],
            'estimated_revenue': clip_data['earning_analysis']['estimated_revenue'],
            'niche': clip_data['niche'],
            'publish_results': publish_results
        }
        
        self.state['published_videos'].append(published_entry)
        self.state['total_published'] += 1
        self.state['last_published'] = datetime.now().isoformat()
        
        # Update daily count
        today = datetime.now().strftime('%Y-%m-%d')
        self.state['daily_count'][today] = self.state['daily_count'].get(today, 0) + 1
        
        # Add to publishing history
        self.state['publishing_history'].append({
            'timestamp': datetime.now().isoformat(),
            'clip_id': clip_data['clip_id'],
            'success_count': publish_results['success_count'],
            'total_count': publish_results['total_count'],
            'earning_score': clip_data['earning_analysis']['final_earning_score'],
            'estimated_revenue': clip_data['earning_analysis']['estimated_revenue']
        })
        
        # Keep only last 100 entries to prevent file from growing too large
        if len(self.state['publishing_history']) > 100:
            self.state['publishing_history'] = self.state['publishing_history'][-100:]
        
        # Save updated state
        self._save_state()

    def run_smart_publishing(self) -> Dict[str, Any]:
        """Run the complete smart publishing process."""
        logger.info("=" * 60)
        logger.info("🚀 STARTING SMART 1-VIDEO PUBLISHING")
        logger.info("=" * 60)
        
        try:
            # Step 1: Load available clips
            logger.info("\n📂 Step 1: Loading available clips...")
            all_clips = self._load_clip_data()
            
            if not all_clips:
                logger.warning("❌ No clips found to publish")
                return {
                    'success': False,
                    'error': 'No clips available',
                    'published_count': 0
                }
            
            logger.info(f"✓ Found {len(all_clips)} clips to evaluate")
            
            # Step 2: Apply filters
            logger.info("\n🔍 Step 2: Applying quality filters...")
            filtered_clips = self._apply_filters(all_clips)
            
            if not filtered_clips:
                logger.warning("❌ No clips passed quality filters")
                return {
                    'success': False,
                    'error': 'No clips passed quality filters',
                    'published_count': 0
                }
            
            logger.info(f"✓ {len(filtered_clips)} clips passed quality filters")
            
            # Step 3: Select best clip
            logger.info("\n🎯 Step 3: Selecting best earning clip...")
            selected_clip = self._select_best_clip(filtered_clips)
            
            if not selected_clip:
                logger.error("❌ Failed to select best clip")
                return {
                    'success': False,
                    'error': 'Failed to select best clip',
                    'published_count': 0
                }
            
            # Step 4: Publish to platforms
            logger.info(f"\n🚀 Step 4: Publishing {selected_clip['clip_id']} to platforms...")
            publish_results = self._publish_to_platforms(selected_clip)
            
            # Step 5: Update state
            logger.info("\n💾 Step 5: Updating publishing state...")
            if publish_results['success_count'] > 0:
                self._update_state(selected_clip, publish_results)
                logger.info("✓ State updated successfully")
            
            # Step 6: Summary
            total_published = self.state['total_published']
            today_count = self.state['daily_count'].get(datetime.now().strftime('%Y-%m-%d'), 0)
            
            logger.info("\n" + "=" * 60)
            logger.info("📊 PUBLISHING SUMMARY")
            logger.info("=" * 60)
            logger.info(f"✓ Published: {publish_results['success_count']}/{publish_results['total_count']} platforms")
            logger.info(f"✓ Clip: {selected_clip['clip_id']}")
            logger.info(f"✓ Earning Score: {selected_clip['earning_analysis']['final_earning_score']:.1f}/100")
            logger.info(f"✓ Estimated Revenue: ${selected_clip['earning_analysis']['estimated_revenue']:.2f}")
            logger.info(f"✓ Expected Views: {selected_clip['earning_analysis']['expected_views']:,}")
            logger.info(f"✓ Niche: {selected_clip['niche']} (CPM: ${selected_clip['earning_analysis']['base_cpm']:.1f})")
            logger.info(f"📈 Total published: {total_published}")
            logger.info(f"📅 Published today: {today_count}")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'published_clip': selected_clip,
                'publish_results': publish_results,
                'earning_analysis': selected_clip['earning_analysis'],
                'total_published': total_published,
                'daily_count': today_count,
                'success_count': publish_results['success_count'],
                'total_count': publish_results['total_count']
            }
            
        except Exception as e:
            logger.error(f"❌ Smart publishing failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'published_count': 0
            }

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current publishing state."""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        return {
            'total_published': self.state['total_published'],
            'published_today': self.state['daily_count'].get(today, 0),
            'published_yesterday': self.state['daily_count'].get(yesterday, 0),
            'last_published': self.state['last_published'],
            'recent_published': self.state['published_videos'][-5:] if self.state['published_videos'] else [],
            'publishing_rate_7_days': sum(self.state['daily_count'].get((datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(7))
        }

def main():
    """Main entry point for smart publisher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart 1-Video Publisher')
    parser.add_argument('--clips-dir', default='data/clips', help='Directory containing clip data')
    parser.add_argument('--state-file', default='data/publishing_state.json', help='State file path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be published without actually publishing')
    
    args = parser.parse_args()
    
    # Initialize smart publisher
    publisher = SmartPublisher(state_file=args.state_file)
    
    # Show state summary
    state_summary = publisher.get_state_summary()
    print(f"\n📊 Current State:")
    print(f"  Total published: {state_summary['total_published']}")
    print(f"  Published today: {state_summary['published_today']}")
    print(f"  Last published: {state_summary['last_published'] or 'Never'}")
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - No actual publishing")
        # Load and show what would be selected
        all_clips = publisher._load_clip_data(args.clips_dir)
        filtered_clips = publisher._apply_filters(all_clips)
        
        if filtered_clips:
            best_clip = publisher._select_best_clip(filtered_clips)
            if best_clip:
                print(f"\n🎯 Would select: {best_clip['clip_id']}")
                print(f"  Earning Score: {best_clip['earning_analysis']['final_earning_score']:.1f}/100")
                print(f"  Estimated Revenue: ${best_clip['earning_analysis']['estimated_revenue']:.2f}")
                print(f"  Expected Views: {best_clip['earning_analysis']['expected_views']:,}")
        else:
            print(f"\n❌ No clips would pass filters")
    else:
        # Run actual smart publishing
        results = publisher.run_smart_publishing()
        
        if results['success']:
            print(f"\n✅ Smart publishing completed successfully!")
            print(f"Published {results['success_count']}/{results['total_count']} platforms")
        else:
            print(f"\n❌ Smart publishing failed: {results['error']}")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())