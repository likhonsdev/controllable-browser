"""
Base AI Provider Interface

This module defines the base interface that all AI providers must implement.
"""

class BaseAIProvider:
    """Base class for all AI providers."""
    
    def __init__(self, api_key, **kwargs):
        """Initialize the AI provider with API key and additional configuration."""
        self.api_key = api_key
        self.config = kwargs
    
    def create_action_plan(self, user_input):
        """Create an action plan based on the user's input."""
        raise NotImplementedError("Subclasses must implement create_action_plan()")
    
    def generate_response(self, prompt):
        """Generate a direct response to a prompt."""
        raise NotImplementedError("Subclasses must implement generate_response()")
    
    def process_content(self, content, user_input, processing_goal):
        """Process web content based on the user's input and processing goal."""
        raise NotImplementedError("Subclasses must implement process_content()")
