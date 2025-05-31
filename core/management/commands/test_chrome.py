from django.core.management.base import BaseCommand
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class Command(BaseCommand):
    help = 'Test Chrome and ChromeDriver installation'

    def handle(self, *args, **options):
        self.stdout.write("🚂 Testing Chrome installation on Railway...")
        
        # Check environment variables
        self.stdout.write("\n📋 Environment Variables:")
        chrome_bin = os.environ.get("CHROME_BIN", "Not set")
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "Not set")
        railway_env = os.environ.get("RAILWAY_ENVIRONMENT", "Not set")
        
        self.stdout.write(f"   CHROME_BIN: {chrome_bin}")
        self.stdout.write(f"   CHROMEDRIVER_PATH: {chromedriver_path}")
        self.stdout.write(f"   RAILWAY_ENVIRONMENT: {railway_env}")
        
        # Check file existence
        self.stdout.write("\n📁 File Existence:")
        chrome_paths = [
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome",
            chrome_bin if chrome_bin != "Not set" else None
        ]
        
        chromedriver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            chromedriver_path if chromedriver_path != "Not set" else None
        ]
        
        self.stdout.write("   Chrome binary:")
        for path in chrome_paths:
            if path and os.path.exists(path):
                self.stdout.write(f"     ✅ {path} - exists")
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
                    self.stdout.write(f"        Version: {result.stdout.strip()}")
                except Exception as e:
                    self.stdout.write(f"        Error getting version: {e}")
            elif path:
                self.stdout.write(f"     ❌ {path} - not found")
        
        self.stdout.write("   ChromeDriver binary:")
        for path in chromedriver_paths:
            if path and os.path.exists(path):
                self.stdout.write(f"     ✅ {path} - exists")
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
                    self.stdout.write(f"        Version: {result.stdout.strip()}")
                except Exception as e:
                    self.stdout.write(f"        Error getting version: {e}")
            elif path:
                self.stdout.write(f"     ❌ {path} - not found")
        
        # Test basic Chrome functionality
        self.stdout.write("\n🧪 Testing Chrome Driver Creation:")
        try:
            # Setup options for Railway
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--remote-debugging-port=9222")
            
            # Set binary location
            if chrome_bin and chrome_bin != "Not set":
                options.binary_location = chrome_bin
            
            # Try with system ChromeDriver
            if chromedriver_path and chromedriver_path != "Not set" and os.path.exists(chromedriver_path):
                self.stdout.write(f"   Testing with system ChromeDriver: {chromedriver_path}")
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
                self.stdout.write("   ✅ Chrome driver created successfully!")
                
                # Test basic navigation
                driver.get("https://www.google.com")
                title = driver.title
                self.stdout.write(f"   ✅ Navigation test passed - Page title: {title}")
                
                driver.quit()
                self.stdout.write("   ✅ Driver closed successfully")
                
            else:
                self.stdout.write("   ⚠️ System ChromeDriver not available, trying auto-detection...")
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                self.stdout.write("   ✅ Auto-detected Chrome driver created successfully!")
                
                # Test basic navigation
                driver.get("https://www.google.com")
                title = driver.title
                self.stdout.write(f"   ✅ Navigation test passed - Page title: {title}")
                
                driver.quit()
                self.stdout.write("   ✅ Driver closed successfully")
                
        except Exception as e:
            self.stderr.write(f"   ❌ Chrome driver test failed: {e}")
            self.stderr.write(f"      Error type: {type(e).__name__}")
            
            # Try to get more detailed error info
            import traceback
            self.stderr.write("      Full traceback:")
            self.stderr.write(traceback.format_exc())
        
        self.stdout.write("\n🏁 Chrome installation test completed!") 