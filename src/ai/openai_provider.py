"""
OpenAI Provider Implementation

This module provides an implementation of the BaseAIProvider interface for OpenAI models.
"""

import os
import json
import re
import traceback
from pathlib import Path
import sys

# Add parent dir to system path for imports if running this file directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import openai
from src.utils.logger import logger, log_step, log_error, log_ai
from src.ai.base_provider import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    """Provider for interacting with OpenAI models."""
    
    def __init__(self, api_key, model="gpt-3.5-turbo", temperature=0.7, max_tokens=1500):
        """Initialize the OpenAI provider with API key and model configuration."""
        super().__init__(api_key)
        
        if not api_key:
            raise ValueError("OpenAI API Key is required")
            
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configure the client
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"OpenAI provider initialized with model: {model}")
    
    def create_action_plan(self, user_input):
        """Create an action plan based on the user's input."""
        log_ai(f"Creating action plan using OpenAI for: {user_input[:100]}...")
        
        try:
            action_plan_prompt = f"""
You are an AI browser agent that helps users perform tasks on the web.
Your task is to analyze the user's request and break it down into a series of browsing actions.

User Request: "{user_input}"

Create a JSON action plan that contains a list of steps to accomplish this task. Return ONLY the JSON object.
Each action must be one of these types:

1. "answer_directly": For questions that can be answered without browsing. 
   Example: {{"type": "answer_directly", "question": "What is the capital of France?"}}

2. "browse": For navigating to a URL. 
   Example: {{"type": "browse", "url": "https://example.com"}}

3. "extract_content": For extracting content from the current page. 
   Example: {{"type": "extract_content", "processing_goal": "Summarize the article"}}

4. "click": For clicking on an element on the page. 
   Example: {{"type": "click", "selector": "button.submit"}}

5. "type": For typing text into an input field. 
   Example: {{"type": "type", "selector": "input#search", "text": "browser automation"}}

6. "clarify": For when the request needs clarification.
   Example: {{"type": "clarify", "message": "Could you specify which website you want me to search on?"}}

Return the plan as a JSON object with an "actions" array containing the sequence of actions:
{{
  "actions": [
    // Array of action objects
  ]
}}

For complex requests, break them down into multiple steps. For example, "search for browser automation on Google" might become:
1. Browse to Google
2. Type search query
3. Extract content from search results

Only generate a JSON response with properly formatted field names. JSON properties must be enclosed in double quotes.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a browser automation assistant. Respond only with valid JSON."},
                    {"role": "user", "content": action_plan_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_text = response.choices[0].message.content
            
            # Extract JSON from the response (in case it's wrapped in markdown or other text)
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
                
            # Remove any comments
            json_str = re.sub(r'//.*', '', json_str)
            
            # Parse the JSON
            action_plan = json.loads(json_str.strip())
            log_ai(f"Action plan created with {len(action_plan.get('actions', []))} steps")
            
            return action_plan
            
        except json.JSONDecodeError as e:
            log_error(f"Failed to parse action plan JSON: {str(e)}")
            log_error(f"Response was: {response_text[:500]}...")
            return {"actions": [{"type": "answer_directly", "question": user_input}]}
            
        except Exception as e:
            log_error(f"Error creating action plan: {str(e)}")
            log_error(traceback.format_exc())
            return {"actions": [{"type": "answer_directly", "question": user_input}]}
    
    def generate_response(self, prompt):
        """Generate a direct response from OpenAI for a prompt."""
        log_ai(f"Generating response using OpenAI for: {prompt[:100]}...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Error generating response: {str(e)}")
            return f"I was unable to generate a response due to an error: {str(e)}"
    
    def process_content(self, content, user_input, processing_goal):
        """Process web content based on the user's input and processing goal."""
        log_ai(f"Processing content with OpenAI. Goal: {processing_goal}")
        
        try:
            # Truncate content if too long
            max_length = 15000
            truncated_content = content[:max_length]
            
            if len(content) > max_length:
                log_ai(f"Content truncated from {len(content)} to {max_length} characters")
            
            prompt = f"""
User Request: "{user_input}"
Processing Goal: "{processing_goal}"

Content from the website:
--- CONTENT START ---
{truncated_content}
--- CONTENT END ---

Based on the user's request and the processing goal, analyze the content and provide a relevant response.
If the content is too large or complex, focus on the most relevant parts to address the processing goal.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            log_error(f"Error processing content: {str(e)}")
            return f"I was unable to process the content due to an error: {str(e)}"
