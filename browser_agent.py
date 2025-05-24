#!/usr/bin/env python
"""
BrowserAGENT - AI-Powered Browser Automation Agent

Main entry point for the application.
"""

import os
import sys
import json
from pathlib import Path
import logging
import subprocess
import webbrowser
from typing import Dict, Any

def load_env_file(env_path: Path, logger: logging.Logger) -> bool:
    """Load environment variables from a .env file."""
    if not env_path.exists():
        return False
        
    logger.info(f"Loading environment variables from {env_path}")
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        return True
    except Exception as e:
        logger.error(f"Error loading .env file: {str(e)}")
        return False

def load_config(config_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """Load the application configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info("Configuration loaded successfully")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        # Return default configuration
        return {
            "server": {"host": "127.0.0.1", "port": 5000, "debug": False},
            "ai": {
                "defaultProvider": "gemini",
                "providers": {
                    "gemini": {
                        "plannerModel": "gemini-1.5-flash-latest",
                        "processorModel": "gemini-1.5-pro-latest"
                    }
                }
            },
            "browserAgent": {"headless": True, "defaultTimeout": 30000},
            "termux": {"enabled": False, "webView": True, "chromeHeadless": True}
        }

def check_api_keys(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Check if the required API keys are available for at least one provider.
    Returns True if at least one provider has an API key, False otherwise.
    """
    default_provider = config.get('ai', {}).get('defaultProvider', 'gemini')
    provider_found = False
    
    # Check for any API key environment variable
    for provider in config.get('ai', {}).get('providers', {}):
        env_var = f"{provider.upper()}_API_KEY"
        if os.environ.get(env_var):
            if provider == default_provider:
                logger.info(f"Found API key for default provider: {provider}")
            else:
                logger.info(f"Found API key for alternative provider: {provider}")
            provider_found = True
    
    return provider_found

def is_termux() -> bool:
    """Check if running in a Termux environment."""
    return 'TERMUX_VERSION' in os.environ or os.path.exists('/data/data/com.termux')

def adjust_for_termux(config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Adjust configuration for Termux environment if necessary."""
    if not is_termux() or not config.get('termux', {}).get('enabled', False):
        return config
        
    logger.info("Termux environment detected, adjusting configuration")
    
    # Update server host to allow external connections
    config['server']['host'] = '0.0.0.0'
    
    # Ensure browser is set to headless mode
    if config.get('termux', {}).get('chromeHeadless', True):
        config['browserAgent']['headless'] = True
        
    return config

def main():
    """Main function to run the BrowserAGENT."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('browser_agent')
    
    project_dir = Path(__file__).parent
    
    # Load environment variables from .env file
    env_path = project_dir / '.env'
    load_env_file(env_path, logger)
    
    # Load configuration
    config_path = project_dir / 'config' / 'config.json'
    config = load_config(config_path, logger)
    
    # Adjust config for Termux if needed
    config = adjust_for_termux(config, logger)
    
    # Check if at least one API key is available
    if not check_api_keys(config, logger):
        logger.error("No API keys found for any AI provider.")
        logger.error("Please run setup.sh or setup.py first, or manually create a .env file with your API key.")
        logger.error("Example API keys: GEMINI_API_KEY, OPENAI_API_KEY, COHERE_API_KEY, etc.")
        sys.exit(1)
    
    # Import after environment variables are set
    from src.web.flask_server import app, initialize_with_config
    
    # Initialize the server with our configuration
    initialize_with_config(config)
    
    logger.info("Starting BrowserAGENT...")
    
    # Get server host and port from config
    host = config.get('server', {}).get('host', '127.0.0.1')
    port = config.get('server', {}).get('port', 5000)
    debug = config.get('server', {}).get('debug', False)
    
    # Open browser unless we're running in Termux without webView
    in_termux = is_termux()
    show_browser = not in_termux or config.get('termux', {}).get('webView', True)
    
    if show_browser:
        url = f"http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}"
        logger.info(f"Opening browser at {url}")
        
        # Try to open browser in a new tab
        try:
            webbrowser.open_new_tab(url)
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
    else:
        logger.info(f"Browser view disabled. Access the server at http://localhost:{port}")
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
