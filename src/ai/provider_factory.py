"""
AI Provider Factory

This module provides a factory for creating instances of different AI providers
based on configuration.
"""

import os
from typing import Dict, Any, Optional

from src.utils.logger import logger, log_error
from src.ai.base_provider import BaseAIProvider
from src.ai.gemini import GeminiClient

# Import providers dynamically to handle missing dependencies gracefully
providers = {}

try:
    from src.ai.openai_provider import OpenAIProvider
    providers["openai"] = OpenAIProvider
except ImportError:
    logger.warning("OpenAI provider not available. Missing dependencies.")

try:
    from src.ai.cohere_provider import CohereProvider
    providers["cohere"] = CohereProvider
except ImportError:
    logger.warning("Cohere provider not available. Missing dependencies.")

try:
    from src.ai.openrouter_provider import OpenRouterProvider
    providers["openrouter"] = OpenRouterProvider
except ImportError:
    logger.warning("OpenRouter provider not available. Missing dependencies.")

try:
    from src.ai.groq_provider import GroqProvider
    providers["groq"] = GroqProvider
except ImportError:
    logger.warning("Groq provider not available. Missing dependencies.")

# Add Gemini which is our default provider
providers["gemini"] = GeminiClient

class AIProviderFactory:
    """Factory for creating AI provider instances."""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> Optional[BaseAIProvider]:
        """
        Create an AI provider instance based on the provider type and configuration.
        
        Args:
            provider_type: The type of provider to create (e.g., 'gemini', 'openai', etc.)
            config: Configuration dict containing api_key and other provider-specific settings
        
        Returns:
            An instance of a BaseAIProvider implementation or None if creation fails
        """
        provider_type = provider_type.lower()
        
        if provider_type not in providers:
            log_error(f"Unknown AI provider type: {provider_type}")
            return None
        
        # Get the API key for the provider
        api_key_env_var = f"{provider_type.upper()}_API_KEY"
        api_key = os.environ.get(api_key_env_var, config.get("api_key"))
        
        if not api_key:
            log_error(f"API key not found for provider {provider_type}. Please set the {api_key_env_var} environment variable or provide it in the configuration.")
            return None
        
        try:
            # Remove the api_key from the config to avoid duplication
            if "api_key" in config:
                config_copy = config.copy()
                del config_copy["api_key"]
            else:
                config_copy = config
                
            # Create and return the provider instance
            provider_class = providers[provider_type]
            provider = provider_class(api_key=api_key, **config_copy)
            logger.info(f"Successfully created {provider_type} provider")
            return provider
            
        except Exception as e:
            log_error(f"Failed to create {provider_type} provider: {str(e)}")
            return None
