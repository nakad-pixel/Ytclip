#!/usr/bin/env python3
"""
Stealth Downloader: Browser-based video download using Playwright
Fallback method when YouTube captions are not available.
"""

import os
import logging
import time
import random
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available")

try:
    import playwright_stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    logging.warning("Playwright stealth plugin not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StealthDownloader:
    """Download videos using browser automation to avoid bot detection."""
    
    def __init__(self, output_dir: str = 'data/downloads', headless: bool = True):
        """Initialize stealth downloader."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright")
        
        self.output_dir = output_dir
        self.headless = headless
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Browser configuration
        self.browser = None
        self.page = None
        self.context = None
        
    def _initialize_browser(self) -> bool:
        """Initialize browser with stealth settings."""
        try:
            playwright = sync_playwright().start()
            
            # Use Chromium with realistic user agent
            self.browser = playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--single-process',
                    '--no-zygote'
                ]
            )
            
            # Create browser context with realistic settings
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['clipboard-read', 'clipboard-write'],
                geolocation={'longitude': -73.935242, 'latitude': 40.730610},
                color_scheme='light'
            )
            
            self.page = self.context.new_page()
            
            # Apply stealth settings
            if STEALTH_AVAILABLE:
                playwright_stealth.stealth_sync(self.page)
            
            # Additional anti-detection measures
            self._apply_stealth_settings()
            
            logger.info("Browser initialized with stealth settings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def _apply_stealth_settings(self):
        """Apply additional stealth settings to the page."""
        if not self.page:
            return
        
        # Remove web driver flags
        self.page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Mock plugins
        self.page.evaluate("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Mock languages
        self.page.evaluate("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
    
    def _human_like_delay(self):
        """Add random delays to mimic human behavior."""
        time.sleep(random.uniform(0.5, 2.0))
    
    def _human_like_typing(self, text: str):
        """Simulate human-like typing."""
        for char in text:
            self.page.keyboard.press(char)
            time.sleep(random.uniform(0.05, 0.2))
    
    def download_video(self, video_id: str, max_retries: int = 3) -> Optional[str]:
        """Download video using browser automation."""
        if not self.page:
            if not self._initialize_browser():
                return None
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_path = os.path.join(self.output_dir, f"{video_id}.mp4")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Downloading {video_id}")
                
                # Navigate to YouTube
                self.page.goto('https://www.youtube.com', timeout=60000)
                self._human_like_delay()
                
                # Navigate to video
                self.page.goto(url, timeout=60000)
                self._human_like_delay()
                
                # Wait for video to load
                self.page.wait_for_selector('video', timeout=60000)
                self._human_like_delay()
                
                # Click play button (mimic human interaction)
                play_button = self.page.query_selector('button.ytp-play-button')
                if play_button:
                    play_button.click()
                    self._human_like_delay()
                
                # Let video play for a few seconds
                time.sleep(random.uniform(3.0, 5.0))
                
                # Use yt-dlp via browser (more reliable than direct download)
                # We'll use a different approach - download via browser automation
                logger.info("Starting video download via browser...")
                
                # Use a more reliable method - download via yt-dlp in the browser context
                # This is a fallback approach
                download_success = self._download_with_yt_dlp_fallback(video_id, output_path)
                
                if download_success:
                    logger.info(f"✓ Successfully downloaded {video_id}")
                    return output_path
                else:
                    logger.warning(f"Download attempt {attempt + 1} failed")
                    
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout during download attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Download error (attempt {attempt + 1}): {e}")
            
            # Clean up and retry
            self._cleanup_browser()
            time.sleep(random.uniform(5.0, 10.0))  # Wait before retry
        
        logger.error(f"Failed to download {video_id} after {max_retries} attempts")
        return None
    
    def _download_with_yt_dlp_fallback(self, video_id: str, output_path: str) -> bool:
        """Fallback download method using yt-dlp via subprocess."""
        try:
            import subprocess
            
            cmd = [
                'yt-dlp',
                '-f', 'best[height<=720]',
                '-o', output_path,
                '--quiet',
                '--no-warnings',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            # Run with timeout
            result = subprocess.run(cmd, check=True, timeout=300, capture_output=True)
            
            if os.path.exists(output_path):
                return True
            else:
                logger.error(f"yt-dlp completed but file not found: {output_path}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("yt-dlp download timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp failed: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"Fallback download error: {e}")
            return False
    
    def cleanup(self, filepath: str) -> None:
        """Delete downloaded file."""
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up: {filepath}")
    
    def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            
            self.page = None
            self.context = None
            self.browser = None
            logger.info("Browser cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up browser: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self._cleanup_browser()