import os
import sys
import json
import logging
from pathlib import Path
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Import our modules
from src.ai.provider_factory import AIProviderFactory
from src.ai.base_provider import BaseAIProvider
from src.browser.engine import PlaywrightBrowser, RequestsBrowser
from src.utils.logger import setup_logger, log_step, log_error, log_browser, log_ai, clear_task_logs

# Setup logging
os.makedirs(project_root / 'logs', exist_ok=True)
logger = setup_logger(
    'browser_agent', 
    log_file=project_root / 'logs' / f'browser_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

# Initialize Flask app
app = Flask(__name__, 
            template_folder=str(project_root / 'templates'),
            static_folder=str(project_root / 'static'))
CORS(app)

# Global variables
config = {}  # Will be set in initialize_with_config
ai_client = None  # Current AI provider
current_provider_name = None  # Name of current provider
browser = None  # Browser engine

# Global store for the current task's logs
current_task_logs = []
last_processed_url = None
last_screenshot = None
available_providers = []

def initialize_with_config(app_config: Dict[str, Any]) -> None:
    """Initialize the server with the provided configuration."""
    global config, ai_client, current_provider_name, browser, available_providers
    
    # Store the configuration
    config = app_config
    logger.info("Flask server initialized with configuration")
    
    # Get the default AI provider from config
    default_provider = config.get('ai', {}).get('defaultProvider', 'gemini')
    
    # Initialize the AI client
    initialize_ai_provider(default_provider)
    
    # Discover available providers
    detect_available_providers()
    
    # Initialize browser engine - try Playwright, fall back to Requests if needed
    initialize_browser_engine()
    
    # Create screenshots directory
    os.makedirs(project_root / 'static' / 'screenshots', exist_ok=True)

def detect_available_providers():
    """Detect which AI providers are available based on API keys."""
    global available_providers
    
    available_providers = []
    
    for provider in config.get('ai', {}).get('providers', {}):
        env_var = f"{provider.upper()}_API_KEY"
        if os.environ.get(env_var):
            available_providers.append(provider)
            
    logger.info(f"Available AI providers: {', '.join(available_providers) if available_providers else 'None'}")

def initialize_ai_provider(provider_name: str) -> bool:
    """Initialize the AI provider with the given name."""
    global ai_client, current_provider_name
    
    if not provider_name:
        logger.error("No provider name specified")
        return False
    
    # Get the provider config
    provider_config = config.get('ai', {}).get('providers', {}).get(provider_name, {})
    if not provider_config:
        logger.error(f"No configuration found for provider: {provider_name}")
        return False
    
    # Create the provider
    try:
        new_client = AIProviderFactory.create_provider(provider_name, provider_config)
        if new_client:
            ai_client = new_client
            current_provider_name = provider_name
            logger.info(f"Initialized AI provider: {provider_name}")
            return True
        else:
            logger.error(f"Failed to create AI provider: {provider_name}")
            return False
    except Exception as e:
        logger.error(f"Error initializing AI provider {provider_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def initialize_browser_engine():
    """Initialize the browser engine based on configuration."""
    global browser
    
    try:
        browser_config = config.get('browserAgent', {})
        
        browser = PlaywrightBrowser(
            headless=browser_config.get('headless', True),
            user_agent=browser_config.get('userAgent'),
            viewport_size={
                "width": browser_config.get('viewport', {}).get('width', 1280),
                "height": browser_config.get('viewport', {}).get('height', 800)
            },
            timeout=browser_config.get('defaultTimeout', 30000)
        )
        logger.info("Playwright browser engine initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Playwright browser: {str(e)}. Falling back to Requests mode.")
        browser = RequestsBrowser()
        logger.info("Requests browser fallback initialized")

def reset_task_state():
    """Reset the state for a new task"""
    global current_task_logs, last_processed_url, last_screenshot
    current_task_logs = []
    last_processed_url = None
    last_screenshot = None

def process_user_command(user_input):
    """Process a user command through the agent pipeline"""
    global current_task_logs, last_processed_url, last_screenshot, ai_client
    reset_task_state()
    
    if ai_client is None:
        log_error("No AI provider initialized")
        return {
            "final_result": "I couldn't process your request because no AI provider is initialized. Please check your configuration.",
            "logs": current_task_logs,
            "processed_url": None,
            "screenshot": None
        }
    
    log_step("Received user command: " + user_input)
    
    try:
        # Plan the action steps using the current AI provider
        log_step("Planning action steps...")
        action_plan = ai_client.create_action_plan(user_input)
        
        if not action_plan or 'actions' not in action_plan:
            log_error("Failed to create a valid action plan")
            return {
                "final_result": "I couldn't plan how to handle your request. Please try again with a clearer instruction.",
                "logs": current_task_logs,
                "processed_url": None,
                "screenshot": None
            }
        
        log_step(f"Created action plan with {len(action_plan['actions'])} steps")
        
        final_result = "Task completed successfully."
        
        # Execute each action in the plan
        for i, action in enumerate(action_plan['actions']):
            action_type = action.get('type')
            log_step(f"Executing step {i+1}: {action_type}")
            
            if action_type == 'answer_directly':
                question = action.get('question', user_input)
                log_ai(f"Generating direct answer for: {question}")
                final_result = ai_client.generate_response(question)
                log_ai("Answer generated successfully")
                
            elif action_type == 'browse':
                url = action.get('url')
                if not url:
                    log_error("URL not provided for browse action")
                    continue
                    
                log_browser(f"Navigating to URL: {url}")
                result = browser.navigate(url)
                last_processed_url = url
                
                if result.get('success'):
                    log_browser("Navigation successful")
                    
                    # Take a screenshot if using Playwright
                    if isinstance(browser, PlaywrightBrowser):
                        screenshot_path = f"screenshots/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        full_path = browser.take_screenshot(project_root / 'static' / screenshot_path)
                        if full_path:
                            last_screenshot = screenshot_path
                            log_step(f"Screenshot captured and saved")
                else:
                    log_error(f"Failed to navigate: {result.get('error')}")
                
            elif action_type == 'extract_content':
                log_browser("Extracting content from current page")
                content = browser.get_content()
                
                if content:
                    log_browser("Content extracted successfully")
                    processing_goal = action.get('processing_goal', 'Analyze the content')
                    
                    log_ai(f"Processing content for: {processing_goal}")
                    final_result = ai_client.process_content(content, user_input, processing_goal)
                    log_ai("Content processing completed")
                else:
                    log_error("Failed to extract content")
                    final_result = "I couldn't extract content from the page."
                    
            elif action_type == 'click':
                selector = action.get('selector')
                if not selector:
                    log_error("Selector not provided for click action")
                    continue
                    
                log_browser(f"Clicking element: {selector}")
                result = browser.click(selector)
                
                if result.get('success'):
                    log_browser("Click successful")
                    
                    # Take a screenshot after clicking
                    if isinstance(browser, PlaywrightBrowser):
                        screenshot_path = f"screenshots/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        full_path = browser.take_screenshot(project_root / 'static' / screenshot_path)
                        if full_path:
                            last_screenshot = screenshot_path
                            log_step(f"Screenshot captured after click")
                else:
                    log_error(f"Failed to click: {result.get('error')}")
                    
            elif action_type == 'type':
                selector = action.get('selector')
                text = action.get('text')
                
                if not selector or not text:
                    log_error("Selector or text not provided for type action")
                    continue
                    
                log_browser(f"Typing '{text}' into: {selector}")
                result = browser.type(selector, text)
                
                if result.get('success'):
                    log_browser("Typing successful")
                else:
                    log_error(f"Failed to type: {result.get('error')}")
                    
            elif action_type == 'clarify':
                message = action.get('message', "Could you please clarify your request?")
                log_step(f"Clarification needed: {message}")
                final_result = message
                
            else:
                log_error(f"Unknown action type: {action_type}")
                
        return {
            "final_result": final_result,
            "logs": current_task_logs,
            "processed_url": last_processed_url,
            "screenshot": last_screenshot
        }
        
    except Exception as e:
        error_msg = f"Error processing command: {str(e)}"
        log_error(error_msg)
        log_error(traceback.format_exc())
        
        return {
            "final_result": "I encountered an error while processing your request. Please try again.",
            "logs": current_task_logs,
            "processed_url": last_processed_url,
            "screenshot": last_screenshot
        }

# Flask routes
@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/command', methods=['POST'])
def handle_command():
    """API endpoint to handle user commands"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.json
    user_command = data.get('command')
    
    if not user_command:
        return jsonify({"error": "No command provided"}), 400
        
    result = process_user_command(user_command)
    return jsonify(result)

@app.route('/api/providers', methods=['GET'])
def get_available_providers():
    """Get available AI providers"""
    return jsonify({
        "providers": available_providers,
        "current": current_provider_name,
        "default": config.get('ai', {}).get('defaultProvider', 'gemini')
    })

@app.route('/api/providers/switch', methods=['POST'])
def switch_ai_provider():
    """Switch to a different AI provider"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.json
    provider = data.get('provider')
    
    if not provider:
        return jsonify({"error": "No provider specified"}), 400
        
    if provider not in available_providers:
        return jsonify({"error": f"Provider '{provider}' is not available"}), 400
    
    if provider == current_provider_name:
        return jsonify({"message": f"Already using {provider}"})
    
    success = initialize_ai_provider(provider)
    
    if success:
        return jsonify({"message": f"Successfully switched to {provider}"})
    else:
        return jsonify({"error": f"Failed to switch to {provider}"}), 500

@app.route('/static/screenshots/<path:filename>')
def serve_screenshot(filename):
    """Serve screenshot files"""
    return send_from_directory(project_root / 'static' / 'screenshots', filename)

if __name__ == '__main__':
    host = config['server'].get('host', '0.0.0.0')
    port = config['server'].get('port', 5000)
    debug = config['server'].get('debug', False)
    
    print(f"Starting BrowserAGENT server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
