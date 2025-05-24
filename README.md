# Controllable-Browser

An AI-powered browser automation agent that combines the capabilities of Playwright, multiple AI models, and a modern web interface to automate browser tasks with natural language commands. Works on Windows, macOS, Linux, and Android via Termux.

## 🚀 Features

- **Modern Web Interface**
  - Responsive UI built with Tailwind CSS
  - Real-time activity logging
  - Browser view with screenshot capabilities
  - Command input and results display

- **Multi-AI Provider Support**
  - Google's Gemini AI models
  - OpenAI GPT models
  - Cohere models
  - Groq models
  - OpenRouter API (accessing multiple models)
  - Easy switching between providers

- **Browser Control**
  - Playwright integration for full browser automation
  - Fallback to Requests+BeautifulSoup for simple tasks
  - Screenshot capabilities
  - Element interaction (clicking, typing, etc.)

- **Robust Architecture**
  - Modular design with clear separation of concerns
  - Comprehensive logging system
  - Error handling and recovery
  - Cross-platform support (Windows, macOS, Linux, Android via Termux)

## 🛠️ Project Structure

```
controllable-browser/
├── src/                      # Source code
│   ├── ai/                   # AI integration
│   │   ├── base_provider.py  # Base class for AI providers
│   │   ├── provider_factory.py # Factory to create providers
│   │   ├── gemini.py         # Google Gemini integration
│   │   ├── openai_provider.py # OpenAI integration
│   │   ├── cohere_provider.py # Cohere integration
│   │   ├── groq_provider.py  # Groq integration
│   │   └── openrouter_provider.py # OpenRouter integration
│   ├── browser/              # Browser automation
│   ├── utils/                # Utilities
│   └── web/                  # Web server
├── static/                   # Static assets
│   ├── js/                   # JavaScript
│   └── screenshots/          # Generated screenshots
├── templates/                # HTML templates
├── config/                   # Configuration
├── browser_agent.py          # Main entry point
├── setup.sh                  # Setup script for Unix
├── setup.py                  # Setup script for Windows
├── run.bat                   # Run script for Windows
└── README.md                 # Documentation
```

## 🚦 Getting Started

### Prerequisites

- Python 3.8 or higher
- At least one API key from a supported AI provider:
  - Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))
  - OpenAI API key ([OpenAI Platform](https://platform.openai.com/))
  - Cohere API key ([Cohere](https://cohere.com/))
  - Groq API key ([Groq Console](https://console.groq.com/))
  - OpenRouter API key ([OpenRouter](https://openrouter.ai/))

### Setup

#### On Windows:
```bash
python setup.py
```

#### On Linux/macOS:
```bash
chmod +x setup.sh
./setup.sh
```

#### On Android (Termux):
```bash
pkg install python
pkg install git
git clone https://github.com/likhonsdev/controllable-browser.git
cd controllable-browser
pip install -r requirements.txt
# Then edit .env file to add your API key(s)
```

### Running the Application

#### On Windows:
```bash
run.bat
```
Or:
```bash
python browser_agent.py
```

#### On Linux/macOS/Termux:
```bash
./run.sh
```
Or:
```bash
python browser_agent.py
```

Once running, open your browser and navigate to: http://localhost:5000

## 🎮 Using the Agent

Enter a command in the input field, such as:

- "Go to example.com and extract all the links"
- "Search for browser automation on Google"
- "Tell me about the latest AI advancements"

The agent will:
1. Plan the necessary actions using your selected AI provider
2. Execute those actions using Playwright
3. Show you the results and a detailed activity log

## 🔧 Configuration

The agent's behavior can be customized by editing the `config/config.json` file:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": false
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
  "browserAgent": {
    "headless": true,
    "defaultTimeout": 30000,
    "viewport": {
      "width": 1280,
      "height": 800
    },
    "userAgent": "Mozilla/5.0 ..."
  },
  "termux": {
    "enabled": false,
    "webView": true,
    "chromeHeadless": true
  }
}
```

## 📱 Dependencies

- **Flask**: Web server framework
- **Playwright**: Browser automation
- **BeautifulSoup4**: HTML parsing
- **AI Providers**:
  - Google GenerativeAI: Gemini models integration
  - OpenAI: GPT models integration
  - Cohere: Cohere models integration
  - Groq: Groq models integration
  - Requests (for OpenRouter API)
- **Tailwind CSS**: UI styling (loaded via CDN)

## 🛑 Limitations

- The agent operates within the constraints of the AI models and Playwright's capabilities
- Complex multi-step tasks might require breaking down into simpler commands
- Some websites may have anti-bot measures that prevent automated browsing
- Performance on mobile devices (Termux) may be limited

## 📝 License

This project is released under the MIT License.
