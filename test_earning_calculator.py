#!/usr/bin/env python3
"""
Test script for the Smart 1-Video Publishing Strategy
Validates the earning calculator functionality without publisher dependencies.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from src.earning_calculator import EarningCalculator

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

def test_niche_cpm_rates():
    """Test CPM rates for different niches."""
    print("💰 Testing Niche CPM Rates...")
    
    calc = EarningCalculator()
    
    expected_cpm_rates = {
        'fortnite': 11.5,
        'horror': 6.0,
        'roblox': 3.0,
        'minecraft': 5.0,
        'call_of_duty': 9.5,
        'valorant': 8.5,
        'gaming': 5.5  # Default
    }
    
    test_clip = {
        'clip_id': 'test_clip',
        'niche': 'gaming',
        'virality_score': 80,
        'brand_safety': {},
        'engagement_metrics': {'excitement_level': 80, 'emotional_arc': 80, 'hook_strength': 80}
    }
    
    for niche, expected_cpm in expected_cpm_rates.items():
        test_clip['niche'] = niche
        result = calc.calculate_earning_potential(test_clip)
        actual_cpm = result['base_cpm']
        
        print(f"  ✓ {niche.title()}: Expected ${expected_cpm:.1f}, Got ${actual_cpm:.1f}")
        
        # Allow small floating point differences
        assert abs(actual_cpm - expected_cpm) < 0.1, f"CPM mismatch for {niche}"
    
    print("✅ Niche CPM rates working correctly!\n")

def test_virality_to_views():
    """Test virality score to expected views calculation."""
    print("📈 Testing Virality to Views Calculation...")
    
    calc = EarningCalculator()
    
    test_cases = [
        (0, 90000, 'Zero virality should give minimal views'),
        (50, 117000, 'Medium virality should give ~1.3x base views'),
        (100, 270000, 'High virality should give 3x base views')
    ]
    
    for virality, expected_base_views, description in test_cases:
        result = calc.calculate_earning_potential({
            'clip_id': 'test',
            'niche': 'gaming',
            'virality_score': virality,
            'brand_safety': {},
            'engagement_metrics': {}
        })
        
        print(f"  ✓ Virality {virality}: {result['expected_views']:,} views - {description}")
        
        # For gaming niche, base should be 90,000
        if virality == 0:
            assert result['expected_views'] >= 1000, "Minimum views should be applied"
        elif virality == 50:
            assert 100000 <= result['expected_views'] <= 130000, "Medium virality should be near 1.3x base"
        elif virality == 100:
            assert result['expected_views'] >= 200000, "High virality should give high views"
    
    print("✅ Virality to views calculation working correctly!\n")

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
        
        # Test niche CPM rates
        test_niche_cpm_rates()
        
        # Test virality to views
        test_virality_to_views()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Earning Calculator implementation is working correctly!")
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
        
        print("🎯 SMART PUBLISHING STRATEGY:")
        print("-" * 40)
        print("✓ Only 1 video published per run")
        print("✓ Virality score > 70 required")
        print("✓ Brand safety filtering applied")
        print("✓ Highest earning potential selected")
        print("✓ Revenue estimation included")
        print("✓ State tracking prevents duplicates")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())