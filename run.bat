@echo off
rem BrowserAGENT Runner for Windows
echo Starting BrowserAGENT...
python browser_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start BrowserAGENT.
    echo Please make sure you have run setup.py first.
    pause
    exit /b %ERRORLEVEL%
)
