#!/usr/bin/env python3
"""
Utils: Common utility functions
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_dir(path: str) -> str:
    """Ensure directory exists, create if not."""
    os.makedirs(path, exist_ok=True)
    return path

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """Load JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return None

    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {e}")
        return None

def save_json(filepath: str, data: Dict[str, Any]) -> bool:
    """Save data to JSON file."""
    try:
        ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")
        return False

def get_file_hash(filepath: str) -> Optional[str]:
    """Get MD5 hash of file."""
    if not os.path.exists(filepath):
        return None

    try:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return None

def format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def format_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def get_timestamp() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value."""
    if denominator == 0:
        return default
    return numerator / denominator

def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def parse_iso_datetime(iso_string: str) -> Optional[datetime]:
    """Parse ISO datetime string."""
    try:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except Exception as e:
        logger.error(f"Error parsing datetime: {e}")
        return None

def calculate_engagement_rate(likes: int, views: int, comments: int = 0) -> float:
    """Calculate engagement rate."""
    if views == 0:
        return 0.0
    return round(((likes + comments) / views) * 100, 2)

def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    value = os.getenv(var_name)
    if value is None:
        if default is not None:
            logger.debug(f"Using default for {var_name}: {default}")
            return default
        logger.warning(f"Environment variable not set: {var_name}")
    return value

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries recursively."""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result

def validate_url(url: str) -> bool:
    """Basic URL validation."""
    return url.startswith(('http://', 'https://'))

def sanitize_filename_for_path(filename: str) -> str:
    """Sanitize filename for file paths."""
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    return filename

class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        logger.debug(f"Started: {self.name}")
        return self

    def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"Completed: {self.name} ({format_duration(duration)})")

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

class RateLimiter:
    """Simple rate limiter."""

    def __init__(self, calls_per_second: float):
        self.calls_per_second = calls_per_second
        self.last_call = None
        self.min_interval = 1.0 / calls_per_second

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        import time

        if self.last_call:
            elapsed = (datetime.now() - self.last_call).total_seconds()
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)

        self.last_call = datetime.now()

def main():
    """Test utility functions."""
    # Test format_duration
    print(f"90s = {format_duration(90)}")
    print(f"150s = {format_duration(150)}")
    print(f"4000s = {format_duration(4000)}")

    # Test format_number
    print(f"500 = {format_number(500)}")
    print(f"1500 = {format_number(1500)}")
    print(f"2500000 = {format_number(2500000)}")

    # Test Timer
    with Timer("Test Operation"):
        import time
        time.sleep(0.5)

if __name__ == '__main__':
    main()
