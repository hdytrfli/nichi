"""Configuration management for the Video File Organizer application."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from nichi.exceptions import ConfigurationError


class ConfigManager:
    """Manages application configuration from environment variables."""

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._load_environment()

    def _load_environment(self) -> bool:
        """
        Load environment variables in order of precedence:
        1. Current working directory .env
        2. User home directory .env
        3. System environment variables only

        Returns:
            True if .env file was found and loaded, False otherwise
        """
        # Try current working directory first
        current_dir = Path.cwd()
        cwd_env = current_dir / ".env"
        cwd_exists = cwd_env.exists()
        if cwd_exists:
            load_dotenv(cwd_env)
            return True

        # Try user home directory
        home_dir = Path.home()
        home_env = home_dir / ".env"
        home_exists = home_env.exists()
        if home_exists:
            load_dotenv(home_env)
            return True

        # Try common config directories
        config_locations = [
            home_dir / ".config" / "nichi" / ".env",
            Path("/etc/nichi/.env"),  # Linux system-wide
        ]

        for config_path in config_locations:
            path_exists = config_path.exists()
            if path_exists:
                load_dotenv(config_path)
                return True

        # Fall back to system environment variables only
        return False

    def get_api_key(self) -> str:
        """Get Google AI API key from environment."""
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            error_message = (
                "GOOGLE_AI_API_KEY not found. Please set it in:\n"
                "1. Current directory .env file\n"
                "2. Home directory ~/.env file\n"
                "3. System environment variables\n"
                "4. ~/.config/nichi/.env file"
            )
            raise ConfigurationError(
                error_message,
                "GOOGLE_AI_API_KEY",
            )
        return api_key

    def get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value with fallback."""
        config_value = os.getenv(key, default)
        return config_value

    def get_int_config_value(self, key: str, default: Optional[int] = None) -> int:
        """Get integer configuration value with fallback."""
        default_string = str(default) if default is not None else None
        value = self.get_config_value(key, default_string)
        if value is None:
            return default if default is not None else 0
        try:
            int_value = int(value)
            return int_value
        except ValueError as e:
            error_message = "Invalid integer value for %s: %s" % (key, value)
            raise ConfigurationError(error_message, key) from e

    def get_float_config_value(self, key: str, default: Optional[float] = None) -> float:
        """Get float configuration value with fallback."""
        default_string = str(default) if default is not None else None
        value = self.get_config_value(key, default_string)
        if value is None:
            return default if default is not None else 0.0
        try:
            float_value = float(value)
            return float_value
        except ValueError as e:
            error_message = "Invalid float value for %s: %s" % (key, value)
            raise ConfigurationError(error_message, key) from e


# Global configuration instance
config = ConfigManager()
