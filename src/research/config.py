import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    pass

class Config:
    @staticmethod
    def validate_api_keys() -> None:
        """Validate required API keys are present and well-formed"""
        openai_key = os.getenv('OPENAI_API_KEY')
        tavily_key = os.getenv('TAVILY_API_KEY')

        if not openai_key or openai_key == 'your_openai_api_key_here':
            raise ConfigurationError("Invalid or missing OPENAI_API_KEY")
        
        if not tavily_key or not tavily_key.startswith('tvly-'):
            raise ConfigurationError("Invalid or missing TAVILY_API_KEY")
        
        findymail_key = os.getenv('FINDYMAIL_API_KEY')
        if not findymail_key:
            raise ConfigurationError("Invalid or missing FINDYMAIL_API_KEY")

    @staticmethod
    def get_api_key(key_name: str) -> Optional[str]:
        """Safely retrieve API key"""
        value = os.getenv(key_name)
        if not value or value.startswith('your_') or value == '':
            logger.error(f"Missing or invalid {key_name}")
            return None
        return value
