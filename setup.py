#!/usr/bin/env python
"""
BrowserAGENT Setup Script for Windows

This script sets up the BrowserAGENT environment on Windows:
1. Installs required Python packages
2. Installs Playwright browsers
3. Sets up configuration
4. Creates necessary directories
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import getpass

def log_success(message):
    """Print a success message."""
    print(f"\033[92m✓ {message}\033[0m")

def log_info(message):
    """Print an info message."""
    print(f"\033[94mℹ {message}\033[0m")

def log_warning(message):
    """Print a warning message."""
    print(f"\033[93m⚠ {message}\033[0m")

def log_error(message):
    """Print an error message."""
    print(f"\033[91m✗ {message}\033[0m")

def main():
    """Main setup function."""
    print("\n" + "="*70)
    print("\033[1;36m🚀 Setting up BrowserAGENT - AI-Powered Browser Automation Agent 🚀\033[0m")
    print("="*70 + "\n")

    # Create project directories
    log_info("Creating project directories...")
    
    project_dir = Path(__file__).parent
    directories = [
        project_dir / 'src',
        project_dir / 'static' / 'js',
        project_dir / 'static' / 'screenshots',
        project_dir / 'templates',
        project_dir / 'config',
        project_dir / 'logs'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    log_success("Project directories created successfully.")

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        log_warning(f"Python version {python_version.major}.{python_version.minor} detected.")
        log_warning("BrowserAGENT works best with Python 3.8+. Some features might not work properly.")
    else:
        log_success(f"Python {python_version.major}.{python_version.minor} detected.")

    # Install required packages
    log_info("Installing required Python packages...")
    packages = [
        "flask",
        "flask-cors",
        "requests",
        "beautifulsoup4",
        "playwright",
        "python-dotenv",
        "google-generativeai"
    ]

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])
        log_success("Python packages installed successfully.")
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to install Python packages: {e}")
        sys.exit(1)

    # Install Playwright browsers
    log_info("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])
        log_success("Playwright browsers installed successfully.")
    except subprocess.CalledProcessError as e:
        log_warning(f"Failed to install Playwright browsers: {e}")
        log_warning("The agent will fall back to basic requests mode.")
        log_warning("You can try installing Playwright browsers manually later with:")
        log_warning(f"{sys.executable} -m playwright install --with-deps chromium")

    # Configure API Keys
    log_info("Configuring AI Provider API Keys...")
    env_path = project_dir / '.env'
    
    # Check if .env file exists and read existing keys
    existing_keys = {}
    if env_path.exists():
        log_info(".env file already exists.")
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        try:
                            key, value = line.strip().split('=', 1)
                            existing_keys[key] = value
                        except ValueError:
                            pass  # Skip malformed lines
            if existing_keys:
                log_success(f"Found {len(existing_keys)} existing API keys.")
        except Exception as e:
            log_error(f"Failed to read .env file: {e}")
    
    # Define available AI providers
    providers = {
        "GEMINI_API_KEY": {
            "name": "Google Gemini",
            "url": "https://aistudio.google.com/",
            "required": True
        },
        "OPENAI_API_KEY": {
            "name": "OpenAI",
            "url": "https://platform.openai.com/",
            "required": False
        },
        "COHERE_API_KEY": {
            "name": "Cohere",
            "url": "https://cohere.com/",
            "required": False
        },
        "OPENROUTER_API_KEY": {
            "name": "OpenRouter",
            "url": "https://openrouter.ai/",
            "required": False
        },
        "GROQ_API_KEY": {
            "name": "Groq",
            "url": "https://console.groq.com/",
            "required": False
        }
    }
    
    # Prompt for missing required keys and optionally for non-required keys
    updated_keys = False
    for key, info in providers.items():
        if key in existing_keys:
            log_success(f"{info['name']} API Key already configured.")
            continue
            
        if info["required"] or input(f"\nDo you want to configure {info['name']} API Key? (y/n): ").lower() == 'y':
            print(f"\n\033[1;93m🔑 {info['name']} API Key\033[0m")
            print(f"You can get one from {info['url']}")
            
            api_key = getpass.getpass(f"Enter your {info['name']} API Key (press Enter to skip if optional): ")
            
            if api_key:
                existing_keys[key] = api_key
                updated_keys = True
                log_success(f"{info['name']} API Key added.")
            elif info["required"]:
                log_error(f"{info['name']} API Key is required but was not provided.")
                if not any(k.startswith(("GEMINI_", "OPENAI_", "COHERE_", "OPENROUTER_", "GROQ_")) for k in existing_keys):
                    log_error("At least one AI provider API key is required.")
                    sys.exit(1)
    
    # Write updated keys to .env file if changes were made
    if updated_keys or not env_path.exists():
        try:
            with open(env_path, 'w') as f:
                for key, value in existing_keys.items():
                    f.write(f"{key}={value}\n")
            log_success("API Keys saved to .env file.")
        except Exception as e:
            log_error(f"Failed to save API Keys to .env file: {e}")
            sys.exit(1)

    # Create configuration file
    log_info("Creating configuration file...")
    config_path = project_dir / 'config' / 'config.json'
    
    config = {
        "version": "1.0.0",
        "browserAgent": {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 BrowserAGENT/1.0.0",
            "viewport": {
                "width": 1280,
                "height": 800
            },
            "defaultTimeout": 30000,
            "screenshotQuality": 80,
            "headless": True
        },
        "ai": {
            "defaultProvider": "gemini",
            "providers": {
                "gemini": {
                    "plannerModel": "gemini-1.5-flash-latest",
                    "processorModel": "gemini-1.5-pro-latest"
                },
                "openai": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                "cohere": {
                    "model": "command",
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                "openrouter": {
                    "model": "anthropic/claude-3-haiku",
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                "groq": {
                    "model": "llama3-8b-8192",
                    "temperature": 0.7,
                    "max_tokens": 1500
                }
            }
        },
        "server": {
            "host": "127.0.0.1",
            "port": 5000,
            "debug": False
        },
        "termux": {
            "enabled": False,
            "webView": True,
            "chromeHeadless": True
        },
        "logging": {
            "level": "INFO",
            "saveScreenshots": True
        }
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        log_success("Configuration file created successfully.")
    except Exception as e:
        log_error(f"Failed to create configuration file: {e}")
        sys.exit(1)

    # All done
    print("\n" + "="*70)
    print("\033[1;32m✨ BrowserAGENT setup completed! ✨\033[0m")
    print("="*70)
    print("\nTo run the application:")
    print("\033[1;36mpython browser_agent.py\033[0m")
    print("\nThen open your browser and go to:")
    print("\033[1;36mhttp://localhost:5000\033[0m\n")

if __name__ == "__main__":
    main()
