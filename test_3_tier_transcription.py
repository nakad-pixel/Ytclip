#!/usr/bin/env python3
"""
Test script to verify 3-tier transcription system integration
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all new imports work correctly."""
    logger.info("🧪 Testing imports...")
    
    try:
        from transcription_api import YouTubeCaptionFetcher
        logger.info("✅ transcription_api imports successfully")
    except ImportError as e:
        logger.error(f"❌ transcription_api import failed: {e}")
        return False
    
    try:
        from stealth_downloader import StealthDownloader
        logger.info("✅ stealth_downloader imports successfully")
    except ImportError as e:
        logger.error(f"❌ stealth_downloader import failed: {e}")
        return False
    
    try:
        from processor import VideoProcessor
        logger.info("✅ processor imports successfully")
    except ImportError as e:
        logger.error(f"❌ processor import failed: {e}")
        return False
    
    return True

def test_3_tier_method():
    """Test that the 3-tier transcription method exists."""
    logger.info("🧪 Testing 3-tier method...")
    
    try:
        from processor import VideoProcessor
        
        # Create processor instance
        processor = VideoProcessor()
        
        # Check if method exists
        if hasattr(processor, '_get_transcription'):
            logger.info("✅ _get_transcription method exists")
            
            # Check if it's callable
            if callable(getattr(processor, '_get_transcription')):
                logger.info("✅ _get_transcription method is callable")
                return True
            else:
                logger.error("❌ _get_transcription method is not callable")
                return False
        else:
            logger.error("❌ _get_transcription method does not exist")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing 3-tier method: {e}")
        return False

def test_processor_initialization():
    """Test that processor initializes correctly with new imports."""
    logger.info("🧪 Testing processor initialization...")
    
    try:
        from processor import VideoProcessor
        
        # Create processor instance
        processor = VideoProcessor()
        
        # Check basic attributes
        if hasattr(processor, 'downloader'):
            logger.info("✅ Processor has downloader")
        else:
            logger.error("❌ Processor missing downloader")
            return False
            
        if hasattr(processor, 'db'):
            logger.info("✅ Processor has database")
        else:
            logger.error("❌ Processor missing database")
            return False
        
        logger.info("✅ Processor initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing processor: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting 3-tier transcription integration tests")
    logger.info("="*60)
    
    tests = [
        ("Import Test", test_imports),
        ("3-Tier Method Test", test_3_tier_method),
        ("Processor Initialization Test", test_processor_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    logger.info("\n" + "="*60)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! 3-tier transcription integration successful!")
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    exit(main())