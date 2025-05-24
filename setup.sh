#!/bin/bash

echo -e "\033[1;34m🚀 Setting up BrowserAGENT - Advanced Web Automation Agent 🚀\033[0m"
echo "This script will create a Playwright-powered browser automation agent with Flask backend and Tailwind CSS frontend."
echo "----------------------------------------------------------------------"

# --- Configuration ---
PROJECT_DIR=$(pwd)
SRC_DIR="$PROJECT_DIR/src"
STATIC_DIR="$PROJECT_DIR/static"
TEMPLATES_DIR="$PROJECT_DIR/templates"
CONFIG_DIR="$PROJECT_DIR/config"

# --- Helper Functions ---
log_error() {
    echo -e "\033[1;31m❌ Error: $1\033[0m"
}

log_success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

log_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

log_warning() {
    echo -e "\033[0;33m⚠️  $1\033[0m"
}

# --- 1. Check Environment ---
echo -e "\n\033[1;33m[1/7] Checking environment...\033[0m"

# Check Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    log_error "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Determine Python command (python or python3)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    log_warning "Python version $PYTHON_VERSION detected. BrowserAGENT works best with Python 3.8+. Some features might not work properly."
else
    log_success "Python $PYTHON_VERSION detected."
fi

# Check pip
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    log_error "pip is not installed. Please install pip."
    exit 1
fi

# Determine pip command (pip or pip3)
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

log_success "Environment check completed successfully."

# --- 2. Install Dependencies ---
echo -e "\n\033[1;33m[2/7] Installing Python dependencies...\033[0m"

log_info "Installing required Python packages..."
$PIP_CMD install flask flask-cors requests beautifulsoup4 playwright python-dotenv google-generativeai

if [ $? -ne 0 ]; then
    log_error "Failed to install required Python packages. Please check your internet connection and try again."
    exit 1
fi

log_info "Installing Playwright browsers..."
$PYTHON_CMD -m playwright install --with-deps chromium

if [ $? -ne 0 ]; then
    log_warning "Failed to install Playwright browsers. The agent will fall back to basic requests mode."
    log_warning "You can try installing Playwright browsers manually later with: $PYTHON_CMD -m playwright install --with-deps chromium"
else
    log_success "Playwright browsers installed successfully."
fi

log_success "All dependencies installed successfully."

# --- 3. Configure AI Provider API Keys ---
echo -e "\n\033[1;33m[3/7] Configuring AI Provider API Keys...\033[0m"
ENV_FILE="$PROJECT_DIR/.env"
KEYS_UPDATED=false

# Check if .env file exists and load environment variables
if [ -f "$ENV_FILE" ]; then
    log_info "Environment file (.env) already exists."
    source "$ENV_FILE" 2>/dev/null || true
    
    # Display found keys
    FOUND_KEYS=0
    for KEY_NAME in GEMINI_API_KEY OPENAI_API_KEY COHERE_API_KEY OPENROUTER_API_KEY GROQ_API_KEY; do
        if [ -n "${!KEY_NAME}" ]; then
            FOUND_KEYS=$((FOUND_KEYS+1))
        fi
    done
    
    if [ $FOUND_KEYS -gt 0 ]; then
        log_success "Found $FOUND_KEYS API key(s) in environment file."
    fi
fi

# Define provider information
declare -A PROVIDERS
PROVIDERS["GEMINI_API_KEY,name"]="Google Gemini"
PROVIDERS["GEMINI_API_KEY,url"]="https://aistudio.google.com/"
PROVIDERS["GEMINI_API_KEY,required"]="true"

PROVIDERS["OPENAI_API_KEY,name"]="OpenAI"
PROVIDERS["OPENAI_API_KEY,url"]="https://platform.openai.com/"
PROVIDERS["OPENAI_API_KEY,required"]="false"

PROVIDERS["COHERE_API_KEY,name"]="Cohere"
PROVIDERS["COHERE_API_KEY,url"]="https://cohere.com/"
PROVIDERS["COHERE_API_KEY,required"]="false"

PROVIDERS["OPENROUTER_API_KEY,name"]="OpenRouter"
PROVIDERS["OPENROUTER_API_KEY,url"]="https://openrouter.ai/"
PROVIDERS["OPENROUTER_API_KEY,required"]="false"

PROVIDERS["GROQ_API_KEY,name"]="Groq"
PROVIDERS["GROQ_API_KEY,url"]="https://console.groq.com/"
PROVIDERS["GROQ_API_KEY,required"]="false"

# Process each provider
for KEY_NAME in GEMINI_API_KEY OPENAI_API_KEY COHERE_API_KEY OPENROUTER_API_KEY GROQ_API_KEY; do
    PROVIDER_NAME="${PROVIDERS["$KEY_NAME,name"]}"
    PROVIDER_URL="${PROVIDERS["$KEY_NAME,url"]}"
    REQUIRED="${PROVIDERS["$KEY_NAME,required"]}"
    
    # Skip if key already exists
    if [ -n "${!KEY_NAME}" ]; then
        log_success "$PROVIDER_NAME API Key already configured."
        continue
    fi
    
    # Ask if the user wants to configure this provider (if not required)
    if [ "$REQUIRED" = "true" ] || { read -p "Do you want to configure $PROVIDER_NAME API Key? (y/n): " CONFIGURE && [ "$CONFIGURE" = "y" ]; }; then
        echo -e "\n🔑 $PROVIDER_NAME API Key"
        echo "You can get one from $PROVIDER_URL"
        read -p "Enter your $PROVIDER_NAME API Key (press Enter to skip if optional): " API_KEY
        
        if [ -n "$API_KEY" ]; then
            # Store the key in environment for current session
            export "$KEY_NAME"="$API_KEY"
            # Mark for saving to .env file
            KEYS_UPDATED=true
            log_success "$PROVIDER_NAME API Key added."
        elif [ "$REQUIRED" = "true" ]; then
            # Check if at least one provider is available
            if ! env | grep -q '_API_KEY='; then
                log_error "$PROVIDER_NAME API Key is required but was not provided."
                log_error "At least one AI provider API key is required."
                exit 1
            fi
        fi
    fi
done

# Save all keys to .env file if any were updated
if [ "$KEYS_UPDATED" = "true" ] || [ ! -f "$ENV_FILE" ]; then
    # Create or clear the env file
    > "$ENV_FILE"
    
    # Write all keys that have values
    for KEY_NAME in GEMINI_API_KEY OPENAI_API_KEY COHERE_API_KEY OPENROUTER_API_KEY GROQ_API_KEY; do
        if [ -n "${!KEY_NAME}" ]; then
            echo "$KEY_NAME=${!KEY_NAME}" >> "$ENV_FILE"
        fi
    done
    
    log_success "API Keys saved to .env file."
fi

# --- 4. Create Configuration File ---
echo -e "\n\033[1;33m[4/7] Creating configuration file...\033[0m"
CONFIG_FILE="$CONFIG_DIR/config.json"

cat > "$CONFIG_FILE" << EOF
{
    "version": "1.0.0",
    "browserAgent": {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 BrowserAGENT/1.0.0",
        "viewport": {
            "width": 1280,
            "height": 800
        },
        "defaultTimeout": 30000,
        "screenshotQuality": 80,
        "headless": true
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
        "host": "0.0.0.0",
        "port": 5000,
        "debug": false
    },
    "termux": {
        "enabled": false,
        "webView": true,
        "chromeHeadless": true
    },
    "logging": {
        "level": "INFO",
        "saveScreenshots": true
    }
}
EOF

log_success "Configuration file created at $CONFIG_FILE"

# --- 5. Create a .gitignore file ---
echo -e "\n\033[1;33m[5/7] Creating .gitignore file...\033[0m"
GITIGNORE_FILE="$PROJECT_DIR/.gitignore"

cat > "$GITIGNORE_FILE" << EOF
# Environment variables
.env
.venv
env/
venv/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Logs
logs/
*.log

# Screenshots
screenshots/

# Editor files
.vscode/
.idea/
*.swp
*.swo

# OS specific
.DS_Store
Thumbs.db
EOF

log_success ".gitignore file created."

# --- 6. Create README.md ---
echo -e "\n\033[1;33m[6/7] Creating README.md...\033[0m"
README_FILE="$PROJECT_DIR/README.md"

cat > "$README_FILE" << EOF
# BrowserAGENT

A powerful browser automation agent with AI capabilities, built with Playwright, Flask, and Gemini AI.

## Features

- Web browsing and interaction through an intuitive UI
- AI-powered task planning and execution
- Full browser automation with Playwright
- Fallback to simple requests mode when needed
- Detailed logging and activity tracking
- Screenshot capabilities

## Quick Start

1. Make sure you have Python 3.8+ installed
2. Run \`./setup.sh\` to install dependencies and set up the project
3. Run \`./run.sh\` to start the agent
4. Open your browser and go to http://localhost:5000

## Usage

Enter a command in the input field and click "Send Command" or press Enter.
The agent will:
1. Plan the necessary steps using Gemini AI
2. Execute those steps (browsing, clicking, typing, etc.)
3. Return the results along with a detailed log of its actions

## Configuration

Edit \`config/config.json\` to customize the agent's behavior.

## License

MIT
EOF

log_success "README.md created."

# --- 7. Create run.sh script ---
echo -e "\n\033[1;33m[7/7] Creating run script...\033[0m"
RUN_SCRIPT="$PROJECT_DIR/run.sh"

cat > "$RUN_SCRIPT" << EOF
#!/bin/bash
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

# Source environment variables
if [ -f "\$SCRIPT_DIR/.env" ]; then
    source "\$SCRIPT_DIR/.env"
fi

# Check for at least one AI provider API key
if [ -z "\$GEMINI_API_KEY" ] && [ -z "\$OPENAI_API_KEY" ] && [ -z "\$COHERE_API_KEY" ] && [ -z "\$OPENROUTER_API_KEY" ] && [ -z "\$GROQ_API_KEY" ]; then
    echo -e "\033[1;31mError: No AI provider API keys found in environment variables or .env file.\033[0m"
    echo "Please run the setup script first or manually create a .env file with at least one API key."
    echo "Supported providers: GEMINI_API_KEY, OPENAI_API_KEY, COHERE_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY"
    exit 1
fi

# Check for Termux environment
if [ -n "\$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
    echo -e "\033[1;33mDetected Termux environment\033[0m"
    
    # If running in Termux, we'll use a different host to allow external connections
    HOST="0.0.0.0" 
    
    # Check if we can open a browser
    if command -v termux-open-url &> /dev/null; then
        echo -e "Will try to open the web interface using termux-open-url"
        termux-open-url "http://localhost:5000" &
    else
        echo -e "Access the web interface at: \033[1;36mhttp://localhost:5000\033[0m"
        echo -e "If you're on a different device, you may need to use your device's IP address instead of localhost."
        ip_address=\$(ip addr | grep 'inet ' | grep -v '127.0.0.1' | awk '{print \$2}' | cut -d/ -f1 | head -n 1)
        if [ -n "\$ip_address" ]; then
            echo -e "Try: \033[1;36mhttp://\$ip_address:5000\033[0m"
        fi
    fi
else
    HOST="127.0.0.1"
    echo -e "\033[0;34m🚀 Launching BrowserAGENT...\033[0m"
    echo -e "-------------------------------------"
    echo -e "Access the web interface at: \033[1;36mhttp://localhost:5000\033[0m"
    
    # Try to open browser automatically
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:5000" &
    elif command -v open &> /dev/null; then
        open "http://localhost:5000" &
    fi
fi

# Run the Flask server
python "\$SCRIPT_DIR/browser_agent.py"
EOF

chmod +x "$RUN_SCRIPT"

if [ -x "$RUN_SCRIPT" ]; then
    log_success "Run script created at $RUN_SCRIPT"
else
    log_error "Failed to create or make executable the run script."
    exit 1
fi

# --- All Done ---
echo -e "\n----------------------------------------------------------------------"
echo -e "\033[1;32m🎉 BrowserAGENT setup completed! 🎉\033[0m"
echo -e "To run the application:"
echo -e "  \033[1;36m./run.sh\033[0m"
echo -e "Then open your browser and go to:"
echo -e "  \033[1;36mhttp://localhost:5000\033[0m"
echo -e "----------------------------------------------------------------------"

exit 0
