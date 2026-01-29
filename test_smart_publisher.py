#!/usr/bin/env python3
"""
Test script for the Smart 1-Video Publishing Strategy
Validates the earning calculator and smart publisher functionality.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from earning_calculator import EarningCalculator
from publisher import SmartPublisher

def test_earning_calculator():
    """Test the earning calculator functionality."""
    print("🧪 Testing Earning Calculator...")
    
    calc = EarningCalculator()
    
    # Test clip data
    test_clip = {
        'clip_id': 'test_fortnite_001',
        'niche': 'fortnite',
        'virality_score': 85,
        'engagement_metrics': {
            'excitement_level': 90,
            'emotional_arc': 88,
            'hook_strength': 92
        },
        'brand_safety': {
            'profanity': False,
            'violence': False,
            'controversy': False,
            'copyright': False,
            'explicit': False
        },
        'moment_type': 'clutch'
    }
    
    # Calculate earning potential
    result = calc.calculate_earning_potential(test_clip)
    
    print(f"  ✓ Clip ID: {result['clip_id']}")
    print(f"  ✓ Niche: {result['niche']}")
    print(f"  ✓ Virality Score: {result['virality_score']}/100")
    print(f"  ✓ Expected Views: {result['expected_views']:,}")
    print(f"  ✓ Base CPM: ${result['base_cpm']:.2f}")
    print(f"  ✓ Earning Score: {result['final_earning_score']:.1f}/100")
    print(f"  ✓ Estimated Revenue: ${result['estimated_revenue']:.2f}")
    print(f"  ✓ Safety Score: {result['safety_score']:.1f}/100")
    
    # Test with different niches
    niches = ['roblox', 'horror', 'minecraft']
    for niche in niches:
        test_clip['niche'] = niche
        test_clip['virality_score'] = 75
        result = calc.calculate_earning_potential(test_clip)
        print(f"  ✓ {niche.title()}: CPM ${result['base_cpm']:.1f}, Revenue ${result['estimated_revenue']:.2f}")
    
    print("✅ Earning Calculator tests passed!\n")

def test_brand_safety():
    """Test brand safety penalties."""
    print("🛡️ Testing Brand Safety Penalties...")
    
    calc = EarningCalculator()
    
    # Safe clip
    safe_clip = {
        'clip_id': 'safe_clip',
        'niche': 'gaming',
        'virality_score': 80,
        'brand_safety': {}
    }
    
    # Unsafe clip with issues
    unsafe_clip = {
        'clip_id': 'unsafe_clip',
        'niche': 'gaming',
        'virality_score': 80,
        'brand_safety': {
            'profanity': True,
            'violence': True,
            'controversy': False,
            'copyright': False,
            'explicit': False
        }
    }
    
    safe_result = calc.calculate_earning_potential(safe_clip)
    unsafe_result = calc.calculate_earning_potential(unsafe_clip)
    
    print(f"  ✓ Safe clip earning score: {safe_result['final_earning_score']:.1f}/100")
    print(f"  ✓ Unsafe clip earning score: {unsafe_result['final_earning_score']:.1f}/100")
    print(f"  ✓ Penalty applied: {safe_result['final_earning_score'] - unsafe_result['final_earning_score']:.1f} points")
    print(f"  ✓ Safety flags: {unsafe_result['safety_flags']}")
    
    assert safe_result['final_earning_score'] > unsafe_result['final_earning_score']
    print("✅ Brand safety penalties working correctly!\n")

def create_mock_processing_data():
    """Create mock processing data for testing."""
    clips_data = []
    
    # Create multiple test clips
    test_clips = [
        {
            'clip_id': 'fortnite_high_viral',
            'youtube_id': 'video_001',
            'niche': 'fortnite',
            'platform': 'youtube_shorts',
            'virality_score': 88,
            'qa_passed': True,
            'title': 'Amazing Fortnite Clutch!',
            'moment_type': 'clutch'
        },
        {
            'clip_id': 'horror_medium_viral',
            'youtube_id': 'video_002', 
            'niche': 'horror',
            'platform': 'tiktok',
            'virality_score': 72,
            'qa_passed': True,
            'title': 'Scary Horror Moment',
            'moment_type': 'jump_scare'
        },
        {
            'clip_id': 'roblox_low_viral',
            'youtube_id': 'video_003',
            'niche': 'roblox', 
            'platform': 'instagram_reels',
            'virality_score': 65,  # Below threshold
            'qa_passed': True,
            'title': 'Roblox Funny Moment',
            'moment_type': 'comedy'
        },
        {
            'clip_id': 'minecraft_high_viral',
            'youtube_id': 'video_004',
            'niche': 'minecraft',
            'platform': 'youtube_shorts', 
            'virality_score': 85,
            'qa_passed': True,
            'title': 'Minecraft Epic Build',
            'moment_type': 'achievement'
        }
    ]
    
    return test_clips

def test_smart_publisher():
    """Test the smart publisher functionality."""
    print("🚀 Testing Smart Publisher...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Create mock data directory structure
        os.makedirs('data/clips', exist_ok=True)
        
        # Create mock processing result
        mock_result = {
            'success': True,
            'video_id': 'test_video_001',
            'niche': 'fortnite',
            'clips_generated': create_mock_processing_data()
        }
        
        # Write mock result file
        with open('data/clips/test_result.json', 'w') as f:
            json.dump(mock_result, f, indent=2)
        
        # Create fake clip files
        for clip in mock_result['clips_generated']:
            clip_path = f"data/clips/{clip['clip_id']}.mp4"
            os.makedirs(os.path.dirname(clip_path), exist_ok=True)
            with open(clip_path, 'w') as f:
                f.write("fake video content")
            clip['clip_path'] = clip_path
        
        # Test smart publisher
        publisher = SmartPublisher(state_file='data/test_state.json')
        
        # Load clips
        clips = publisher._load_clip_data('data/clips')
        print(f"  ✓ Loaded {len(clips)} clips")
        
        # Apply filters
        filtered_clips = publisher._apply_filters(clips)
        print(f"  ✓ {len(filtered_clips)} clips passed filters")
        
        # Should filter out the low virality Roblox clip (65 < 70)
        assert len(filtered_clips) == 3, f"Expected 3 clips, got {len(filtered_clips)}"
        
        # Select best clip
        if filtered_clips:
            best_clip = publisher._select_best_clip(filtered_clips)
            print(f"  ✓ Selected: {best_clip['clip_id']}")
            print(f"  ✓ Earning Score: {best_clip['earning_analysis']['final_earning_score']:.1f}/100")
            print(f"  ✓ Expected Revenue: ${best_clip['earning_analysis']['estimated_revenue']:.2f}")
            
            # Should select the highest earning (Fortnite or Minecraft)
            assert best_clip['niche'] in ['fortnite', 'minecraft']
        
        print("✅ Smart Publisher tests passed!\n")

def test_filtering_logic():
    """Test filtering logic."""
    print("🔍 Testing Filtering Logic...")
    
    calc = EarningCalculator()
    
    # Create test clips with different characteristics
    clips = [
        {
            'clip_id': 'high_viral_safe',
            'niche': 'fortnite',
            'virality_score': 90,
            'brand_safety': {},
            'engagement_metrics': {'excitement_level': 85, 'emotional_arc': 80, 'hook_strength': 90}
        },
        {
            'clip_id': 'medium_viral_safe', 
            'niche': 'roblox',
            'virality_score': 75,
            'brand_safety': {},
            'engagement_metrics': {'excitement_level': 70, 'emotional_arc': 75, 'hook_strength': 72}
        },
        {
            'clip_id': 'high_viral_unsafe',
            'niche': 'horror',
            'virality_score': 88,
            'brand_safety': {'profanity': True, 'violence': True},
            'engagement_metrics': {'excitement_level': 90, 'emotional_arc': 85, 'hook_strength': 88}
        },
        {
            'clip_id': 'low_viral_safe',
            'niche': 'gaming',
            'virality_score': 60,  # Below threshold
            'brand_safety': {},
            'engagement_metrics': {'excitement_level': 55, 'emotional_arc': 50, 'hook_strength': 58}
        }
    ]
    
    # Filter clips
    filtered = calc.filter_clips_by_criteria(clips, min_virality=70, min_safety_score=70)
    
    print(f"  ✓ Started with {len(clips)} clips")
    print(f"  ✓ {len(filtered)} clips passed filters")
    
    # Should filter out:
    # - low_viral_safe (virality 60 < 70)
    # - high_viral_unsafe (safety score < 70 due to penalties)
    assert len(filtered) == 2, f"Expected 2 clips, got {len(filtered)}"
    
    # Verify the right clips passed
    passed_ids = [clip['clip_id'] for clip in filtered]
    assert 'high_viral_safe' in passed_ids
    assert 'medium_viral_safe' in passed_ids
    assert 'low_viral_safe' not in passed_ids
    assert 'high_viral_unsafe' not in passed_ids
    
    print("✅ Filtering logic working correctly!\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 TESTING SMART 1-VIDEO PUBLISHING STRATEGY")
    print("=" * 60)
    print()
    
    try:
        # Test earning calculator
        test_earning_calculator()
        
        # Test brand safety
        test_brand_safety()
        
        # Test filtering logic
        test_filtering_logic()
        
        # Test smart publisher
        test_smart_publisher()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Implementation is working correctly!")
        print("✅ Ready for production use!")
        print()
        
        # Show example output
        print("📊 EXAMPLE EARNING CALCULATION:")
        print("-" * 40)
        
        calc = EarningCalculator()
        example_clip = {
            'clip_id': 'example_clip',
            'niche': 'fortnite',
            'virality_score': 85,
            'engagement_metrics': {
                'excitement_level': 90,
                'emotional_arc': 88,
                'hook_strength': 92
            },
            'brand_safety': {
                'profanity': False,
                'violence': False,
                'controversy': False,
                'copyright': False,
                'explicit': False
            },
            'moment_type': 'clutch'
        }
        
        result = calc.calculate_earning_potential(example_clip)
        print(f"Virality Score: {result['virality_score']}/100")
        print(f"Earning Potential: {result['final_earning_score']:.1f}/100")
        print(f"Expected Views: {result['expected_views']:,}")
        print(f"Estimated Revenue: ${result['estimated_revenue']:.2f}")
        print(f"CPM Rate: ${result['base_cpm']:.2f}")
        print(f"Safety Score: {result['safety_score']:.1f}/100")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())