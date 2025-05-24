import os
import sys
from pathlib import Path
import traceback
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Add parent dir to system path for imports if running this file directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.utils.logger import logger, log_step, log_error, log_browser

class BaseBrowser:
    """Base class for browser interactions."""
    
    def __init__(self):
        """Initialize the base browser."""
        self.current_url = None
    
    def navigate(self, url):
        """Navigate to a URL."""
        raise NotImplementedError("Subclasses must implement navigate()")
    
    def get_content(self):
        """Get the content of the current page."""
        raise NotImplementedError("Subclasses must implement get_content()")
    
    def click(self, selector):
        """Click an element on the page."""
        raise NotImplementedError("Subclasses must implement click()")
    
    def type(self, selector, text):
        """Type text into an input field."""
        raise NotImplementedError("Subclasses must implement type()")
    
    def take_screenshot(self, file_path=None):
        """Take a screenshot of the current page."""
        raise NotImplementedError("Subclasses must implement take_screenshot()")
    
    def close(self):
        """Close the browser."""
        pass


class PlaywrightBrowser(BaseBrowser):
    """Browser implementation using Playwright for full browser automation."""
    
    def __init__(self, headless=True, user_agent=None, viewport_size=None, timeout=30000):
        """Initialize the Playwright browser."""
        super().__init__()
        
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
        except ImportError as e:
            log_error(f"Failed to import playwright: {str(e)}")
            raise ImportError("Playwright is required for the PlaywrightBrowser. Install it with 'pip install playwright'.")
        except Exception as e:
            log_error(f"Failed to start Playwright: {str(e)}")
            raise
        
        try:
            # Set default viewport size if not provided
            if not viewport_size:
                viewport_size = {"width": 1280, "height": 800}
            
            # Launch the browser
            self.browser = self.playwright.chromium.launch(headless=headless)
            
            # Create a browser context with custom options
            context_options = {
                "viewport": viewport_size,
                "accept_downloads": True,
            }
            
            if user_agent:
                context_options["user_agent"] = user_agent
                
            self.context = self.browser.new_context(**context_options)
            
            # Create a new page
            self.page = self.context.new_page()
            
            # Set default timeout
            if timeout:
                self.page.set_default_navigation_timeout(timeout)
                self.page.set_default_timeout(timeout)
            
            logger.info("Playwright browser initialized successfully")
        except Exception as e:
            self.close()
            log_error(f"Failed to initialize Playwright browser: {str(e)}")
            raise
    
    def navigate(self, url):
        """Navigate to a URL."""
        try:
            # Ensure URL starts with http:// or https://
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            log_browser(f"Navigating to URL: {url}")
            response = self.page.goto(url, wait_until="domcontentloaded")
            self.current_url = url
            
            # Wait for page to be fully loaded
            self.page.wait_for_load_state("networkidle", timeout=30000)
            
            return {"success": True}
        except Exception as e:
            log_error(f"Navigation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_content(self):
        """Get the content of the current page."""
        try:
            # Wait for content to stabilize
            self.page.wait_for_load_state("networkidle", timeout=10000)
            
            # Get the HTML content
            content = self.page.content()
            
            # Parse the content with BeautifulSoup to extract the text
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript", "iframe", "svg"]):
                script.decompose()
                
            # Get the text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            return text_content
        except Exception as e:
            log_error(f"Error getting content: {str(e)}")
            return None
    
    def click(self, selector):
        """Click an element on the page."""
        try:
            # Try to scroll the element into view first
            try:
                self.page.evaluate(f"""(selector) => {{
                    const element = document.querySelector(selector);
                    if (element) element.scrollIntoView({{ behavior: "smooth", block: "center" }});
                }}""", selector)
                time.sleep(1)  # Give the page time to scroll
            except Exception as e:
                log_error(f"Error scrolling to element: {str(e)}")
            
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, state="visible")
            
            # Click the element
            self.page.click(selector)
            
            # Wait for any potential navigation or page changes
            time.sleep(2)
            
            return {"success": True}
        except Exception as e:
            log_error(f"Click error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def type(self, selector, text):
        """Type text into an input field."""
        try:
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, state="visible")
            
            # Clear the input field first
            self.page.evaluate(f"""(selector) => {{
                const element = document.querySelector(selector);
                if (element) element.value = '';
            }}""", selector)
            
            # Type the text
            self.page.type(selector, text)
            
            return {"success": True}
        except Exception as e:
            log_error(f"Type error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def take_screenshot(self, file_path=None):
        """Take a screenshot of the current page."""
        try:
            if not file_path:
                screenshots_dir = Path(__file__).resolve().parent.parent.parent / 'static' / 'screenshots'
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = screenshots_dir / f"screenshot_{timestamp}.png"
            
            # Convert to Path object if it's a string
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # Ensure the directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Take the screenshot
            self.page.screenshot(path=str(file_path), full_page=True)
            
            log_browser(f"Screenshot saved to {file_path}")
            return file_path
        except Exception as e:
            log_error(f"Screenshot error: {str(e)}")
            return None
    
    def close(self):
        """Close the browser."""
        try:
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
                
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
                
            logger.info("Playwright browser closed")
        except Exception as e:
            log_error(f"Error closing Playwright browser: {str(e)}")


class RequestsBrowser(BaseBrowser):
    """Simple browser implementation using Requests and BeautifulSoup for basic web scraping."""
    
    def __init__(self, user_agent=None):
        """Initialize the Requests browser."""
        super().__init__()
        
        if not user_agent:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 BrowserAGENT/1.0.0"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def navigate(self, url):
        """Navigate to a URL."""
        try:
            # Ensure URL starts with http:// or https://
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            log_browser(f"Navigating to URL: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            self.current_url = url
            self.current_response = response
            
            return {"success": True}
        except Exception as e:
            log_error(f"RequestsBrowser navigation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_content(self):
        """Get the content of the current page."""
        if not hasattr(self, 'current_response'):
            log_error("No page has been loaded yet")
            return None
        
        try:
            # Create BeautifulSoup object
            soup = BeautifulSoup(self.current_response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript", "iframe", "svg"]):
                script.decompose()
                
            # Get the text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            return text_content
        except Exception as e:
            log_error(f"RequestsBrowser content extraction error: {str(e)}")
            return None
    
    def click(self, selector):
        """Simulate clicking an element by following the href if it's a link."""
        log_error("RequestsBrowser does not support clicking elements. Use PlaywrightBrowser for this feature.")
        return {"success": False, "error": "RequestsBrowser does not support clicking elements"}
    
    def type(self, selector, text):
        """Simulate typing text into an input field."""
        log_error("RequestsBrowser does not support typing text. Use PlaywrightBrowser for this feature.")
        return {"success": False, "error": "RequestsBrowser does not support typing text"}
    
    def take_screenshot(self, file_path=None):
        """Take a screenshot of the current page."""
        log_error("RequestsBrowser does not support taking screenshots. Use PlaywrightBrowser for this feature.")
        return None
