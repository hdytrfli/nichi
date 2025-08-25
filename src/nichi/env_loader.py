"""
Environment configuration loader
Handles .env file detection for both development and installed package usage
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class EnvLoader:
    """Handle environment variable loading from multiple sources"""

    @staticmethod
    def load_env() -> bool:
        """
        Load environment variables in order of precedence:
        1. Current working directory .env
        2. User home directory .env
        3. System environment variables only

        Returns:
            True if .env file was found and loaded, False otherwise
        """
        # Try current working directory first
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            load_dotenv(cwd_env)
            return True

        # Try user home directory
        home_env = Path.home() / ".env"
        if home_env.exists():
            load_dotenv(home_env)
            return True

        # Try common config directories
        config_locations = [
            Path.home() / ".config" / "nichi" / ".env",
            Path("/etc/nichi/.env"),  # Linux system-wide
        ]

        for config_path in config_locations:
            if config_path.exists():
                load_dotenv(config_path)
                return True

        # Fall back to system environment variables only
        return False

    @staticmethod
    def get_api_key() -> str:
        """Get Google AI API key from environment"""
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_AI_API_KEY not found. Please set it in:\n"
                "1. Current directory .env file\n"
                "2. Home directory ~/.env file\n"
                "3. System environment variables\n"
                "4. ~/.config/nichi/.env file"
            )
        return api_key

    @staticmethod
    def get_config_value(key: str, default: str = None) -> str:
        """Get configuration value with fallback"""
        return os.getenv(key, default)
