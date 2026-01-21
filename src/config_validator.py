#!/usr/bin/env python3
"""
Config Validator: Validate configuration files
Ensures all required settings are present and valid.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validate configuration files."""

    REQUIRED_SYSTEM_KEYS = ['name', 'version', 'environment']
    REQUIRED_DISCOVERY_KEYS = ['niches', 'min_views', 'max_age_days']

    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize config validator.

        Args:
            config_path: Path to config file
        """
        self.config_path = config_path

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate configuration file.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check if file exists
        if not os.path.exists(self.config_path):
            errors.append(f"Config file not found: {self.config_path}")
            return False, errors

        # Load config
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML: {e}")
            return False, errors

        # Validate system section
        if 'system' not in config:
            errors.append("Missing 'system' section")
        else:
            errors.extend(self._validate_system(config['system']))

        # Validate discovery section
        if 'discovery' not in config:
            errors.append("Missing 'discovery' section")
        else:
            errors.extend(self._validate_discovery(config['discovery']))

        # Validate video_processing section
        if 'video_processing' not in config:
            errors.append("Missing 'video_processing' section")

        # Validate publishing section
        if 'publishing' not in config:
            errors.append("Missing 'publishing' section")

        # Validate database section
        if 'database' not in config:
            errors.append("Missing 'database' section")

        # Check for environment variables
        errors.extend(self._check_env_variables())

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Configuration is valid")
        else:
            logger.error(f"Configuration errors: {len(errors)}")
            for error in errors:
                logger.error(f"  - {error}")

        return is_valid, errors

    def _validate_system(self, system: Dict[str, Any]) -> List[str]:
        """Validate system configuration."""
        errors = []

        for key in self.REQUIRED_SYSTEM_KEYS:
            if key not in system:
                errors.append(f"Missing system.{key}")

        # Validate environment
        valid_environments = ['development', 'staging', 'production']
        if 'environment' in system and system['environment'] not in valid_environments:
            errors.append(f"Invalid environment: {system['environment']}")

        return errors

    def _validate_discovery(self, discovery: Dict[str, Any]) -> List[str]:
        """Validate discovery configuration."""
        errors = []

        for key in self.REQUIRED_DISCOVERY_KEYS:
            if key not in discovery:
                errors.append(f"Missing discovery.{key}")

        # Validate niches is a list
        if 'niches' in discovery and not isinstance(discovery['niches'], list):
            errors.append("discovery.niches must be a list")

        # Validate numeric values
        if 'min_views' in discovery and not isinstance(discovery['min_views'], int):
            errors.append("discovery.min_views must be an integer")

        if 'max_age_days' in discovery and not isinstance(discovery['max_age_days'], int):
            errors.append("discovery.max_age_days must be an integer")

        return errors

    def _check_env_variables(self) -> List[str]:
        """Check for required environment variables."""
        errors = []

        required_env_vars = [
            'YOUTUBE_API_KEY',
            'GEMINI_API_KEY'
        ]

        optional_env_vars = [
            'YOUTUBE_CLIENT_SECRETS',
            'TIKTOK_ACCESS_TOKEN',
            'INSTAGRAM_ACCESS_TOKEN'
        ]

        for var in required_env_vars:
            if not os.getenv(var):
                errors.append(f"Required environment variable not set: {var}")

        for var in optional_env_vars:
            if not os.getenv(var):
                logger.warning(f"Optional environment variable not set: {var}")

        return errors

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Load and return configuration."""
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            return None

        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return None

def main():
    """Test config validator."""
    validator = ConfigValidator()

    is_valid, errors = validator.validate()

    if is_valid:
        print("✓ Configuration is valid")
        config = validator.get_config()
        print(f"System: {config['system']['name']} v{config['system']['version']}")
    else:
        print("✗ Configuration has errors:")
        for error in errors:
            print(f"  - {error}")

if __name__ == '__main__':
    main()
