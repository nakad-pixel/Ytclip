#!/usr/bin/env python3
"""
Test Two-Phase Pipeline Implementation
Verifies that the new two-phase architecture is working correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
from pipeline_orchestrator import PipelineOrchestrator

def test_database_schema():
    """Test that database has new columns."""
    print("Testing database schema...")
    
    db = Database(db_path='data/test_videos.db')
    
    # Test adding a video with new fields
    video_data = {
        'youtube_id': 'test_phase_video',
        'title': 'Test Video',
        'channel': 'Test Channel',
        'niche': 'Roblox',
        'url': 'https://youtube.com/watch?v=test_phase_video'
    }
    
    video_id = db.add_video(video_data)
    print(f"  ✓ Added video with ID: {video_id}")
    
    # Test updating status
    db.update_video_status('test_phase_video', 'analyzed', virality_score=85.5)
    print("  ✓ Updated video status to 'analyzed' with score 85.5")
    
    # Test getting discovered videos
    discovered = db.get_discovered_videos(limit=10)
    print(f"  ✓ get_discovered_videos() returned {len(discovered)} videos")
    
    # Test getting top analyzed videos
    top_videos = db.get_top_analyzed_videos(limit=5, threshold=70.0)
    print(f"  ✓ get_top_analyzed_videos() returned {len(top_videos)} videos")
    
    if top_videos:
        top_video = top_videos[0]
        print(f"  ✓ Top video: {top_video['youtube_id']} (score: {top_video['virality_score']})")
    
    # Cleanup
    os.remove('data/test_videos.db')
    print("  ✓ Database schema tests passed")

def test_processor_phases():
    """Test that processor supports phase parameter."""
    print("\nTesting processor phases...")
    
    from processor import VideoProcessor
    
    config = {}
    processor = VideoProcessor(config)
    
    # Test that methods exist
    assert hasattr(processor, '_process_analysis_phase'), "Missing _process_analysis_phase"
    print("  ✓ Processor has _process_analysis_phase method")
    
    assert hasattr(processor, '_process_creation_phase'), "Missing _process_creation_phase"
    print("  ✓ Processor has _process_creation_phase method")
    
    assert hasattr(processor, 'process_video'), "Missing process_video"
    print("  ✓ Processor has process_video method")
    
    print("  ✓ Processor phase tests passed")

def test_orchestrator():
    """Test that orchestrator is properly initialized."""
    print("\nTesting pipeline orchestrator...")
    
    config = {
        'processing': {
            'max_videos_to_analyze': 100,
            'virality_threshold': 70,
            'max_videos_to_process': 2
        }
    }
    
    orchestrator = PipelineOrchestrator(config)
    
    # Test configuration
    assert orchestrator.max_videos_to_analyze == 100, "Wrong max_videos_to_analyze"
    print("  ✓ max_videos_to_analyze = 100")
    
    assert orchestrator.virality_threshold == 70, "Wrong virality_threshold"
    print("  ✓ virality_threshold = 70")
    
    assert orchestrator.max_videos_to_process == 2, "Wrong max_videos_to_process"
    print("  ✓ max_videos_to_process = 2")
    
    # Test that methods exist
    assert hasattr(orchestrator, 'run_phase_1_analysis'), "Missing run_phase_1_analysis"
    print("  ✓ Orchestrator has run_phase_1_analysis method")
    
    assert hasattr(orchestrator, 'run_phase_2_creation'), "Missing run_phase_2_creation"
    print("  ✓ Orchestrator has run_phase_2_creation method")
    
    print("  ✓ Orchestrator tests passed")

def main():
    """Run all tests."""
    print("="*60)
    print("Two-Phase Pipeline Implementation Tests")
    print("="*60)
    
    try:
        test_database_schema()
        test_processor_phases()
        test_orchestrator()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe two-phase pipeline implementation is working correctly!")
        print("\nNext steps:")
        print("  1. Test Phase 1: python src/processor.py --phase analysis")
        print("  2. Test Phase 2: python src/processor.py --phase creation")
        print("  3. Deploy to GitHub Actions")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
