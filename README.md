# Stock Web Scraper

## Prerequisites

### PyEnv Setup
1. **Install pyenv** (if not already installed):
   ```bash
   # On macOS with Homebrew
   brew install pyenv
   
   # Or using the automatic installer
   curl https://pyenv.run | bash
   ```

2. **Configure your shell** (add to ~/.zshrc or ~/.bash_profile):
   ```bash
   export PYENV_ROOT="$HOME/.pyenv"
   export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   ```

3. **Restart your shell** or run:
   ```bash
   source ~/.zshrc
   ```

4. **Install Python 3.11.12**:
   ```bash
   pyenv install 3.11.12
   pyenv global 3.11.12
   ```

5. **Verify installation**:
   ```bash
   python --version 
   ```

### Virtual Environment
- Current python version for this project: **3.11.12**
- Create venv: `python -m venv venv` or `/opt/homebrew/bin/python3.11 -m venv venv`
- Activate venv: `source venv/bin/activate`
- Deactivate venv: `deactivate`
- Remove venv: `rm -rf venv`

### Install Dependencies
1. **Activate your virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   pip list
   ```

### Redis Setup
- Install Redis: `brew install redis`
- Start Redis server: `redis-server`

### Database Setup for Celery
- Run Django migrations for Celery results backend: `python manage.py migrate django_celery_results`

### Running celery
- Run venv: `source venv/bin/activate`
- Start Celery: `celery -A stock_scraper worker --loglevel=info -c 4 -n my_worker`

## Environment Configuration

### Scraper Configuration File

The scraper behavior is controlled by `scraper_config.py`. Key settings:

**Browser Display Mode:**
```python
# Set to True to see browser during scraping (debugging)
# Set to False for headless mode (production)
SHOW_BROWSER = True
```

**Debug Settings:**
```python
DEBUG_MODE = True                    # Enable debug logging
SAVE_DEBUG_SCREENSHOTS = True       # Save screenshots on errors
SAVE_DEBUG_PAGE_SOURCE = True       # Save page source on errors
```

**Timeout Settings:**
```python
ELEMENT_WAIT_TIMEOUT = 30           # Wait time for elements (seconds)
PAGE_LOAD_TIMEOUT = 60              # Wait time for page loads (seconds)
```

**Quick Toggle Between Modes:**
- **For Debugging**: Set `SHOW_BROWSER = True` in `scraper_config.py`
- **For Production**: Set `SHOW_BROWSER = False` in `scraper_config.py`

### Chrome Driver Setup
The application automatically detects the environment and uses the appropriate Chrome driver:

**Local Development:**
- Uses local chromedriver: `./chromedriver`
- No environment variables needed
- **Browser Mode**: Controlled by `SHOW_BROWSER` setting in `scraper_config.py`

**Production (Heroku/Cloud):**
- Uses `CHROMEDRIVER_PATH` environment variable
- Set this variable in your production environment
- **Recommended**: Set `SHOW_BROWSER = False` for headless mode

**Example for production:**
```bash
export CHROMEDRIVER_PATH=/app/.chromedriver/bin/chromedriver
```

### Updating ChromeDriver
When Chrome browser updates, you may need to update ChromeDriver to match:

1. **Check Chrome version:**
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
   ```

2. **Download matching ChromeDriver:**
   ```bash
   # Replace 136.0.7103.114 with your Chrome version
   curl -O https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.114/mac-x64/chromedriver-mac-x64.zip
   unzip chromedriver-mac-x64.zip
   mv chromedriver chromedriver_backup
   mv chromedriver-mac-x64/chromedriver ./chromedriver
   chmod +x chromedriver
   rm -rf chromedriver-mac-x64.zip chromedriver-mac-x64/
   ```

3. **Verify version:**
   ```bash
   ./chromedriver --version
   ```

## Package Analysis

### Potentially Unused Packages in requirements.txt

Based on code analysis, the following packages may not be actively used and could potentially be removed:

**Likely Unused:**
- `arrow==1.2.3` - Date/time library (not found in imports)
- `async-generator==1.10` - Async utilities (not found in imports)
- `attrs==22.1.0` - Class utilities (not found in imports)
- `blessed==1.19.1` - Terminal utilities (not found in imports)
- `cachetools==5.2.0` - Caching utilities (not found in imports)
- `gcloud==0.18.3` - Google Cloud (not found in imports)
- `google-auth==2.11.0` - Google authentication (not found in imports)
- `google-auth-oauthlib==0.5.2` - Google OAuth (not found in imports)
- `googleapis-common-protos==1.58.0` - Google API protos (not found in imports)
- `gspread==5.5.0` - Google Sheets API (not found in imports)
- `h11==0.13.0` - HTTP/1.1 library (not found in imports)
- `html5lib==1.1` - HTML parser (not found in imports)
- `httplib2==0.20.4` - HTTP library (not found in imports)
- `Jinja2==3.1.2` - Template engine (not found in imports)
- `jws==0.1.3` - JSON Web Signatures (not found in imports)
- `oauth2client==4.1.3` - OAuth2 client (not found in imports)
- `oauthlib==3.2.1` - OAuth library (not found in imports)
- `outcome==1.2.0` - Async utilities (not found in imports)
- `progress==1.6` - Progress bars (not found in imports)
- `prompt-toolkit==3.0.31` - Command line interface (not found in imports)
- `protobuf==4.21.12` - Protocol buffers (not found in imports)
- `pyasn1==0.4.8` - ASN.1 library (not found in imports)
- `pyasn1-modules==0.2.8` - ASN.1 modules (not found in imports)
- `pycryptodome==3.17` - Cryptography (not found in imports)
- `pyparsing==3.0.9` - Parsing library (not found in imports)
- `PySocks==1.7.1` - SOCKS proxy (not found in imports)
- `python-jwt==2.0.1` - JWT library (not found in imports)
- `rsa==4.9` - RSA cryptography (not found in imports)
- `six==1.15.0` - Python 2/3 compatibility (not found in imports)
- `sniffio==1.2.0` - Async library detection (not found in imports)
- `sortedcontainers==2.4.0` - Sorted containers (not found in imports)
- `trio==0.21.0` - Async library (not found in imports)
- `trio-websocket==0.9.2` - WebSocket for trio (not found in imports)
- `wcwidth==0.2.5` - Terminal width (not found in imports)
- `webencodings==0.5.1` - Web encodings (not found in imports)
- `wsproto==1.1.0` - WebSocket protocol (not found in imports)
- `xlrd==2.0.1` - Excel reader (not found in imports)
- `xlwt==1.3.0` - Excel writer (not found in imports)

**Currently Used Packages:**
- Django and related packages
- Selenium and webdriver-manager
- BeautifulSoup4 for web scraping
- Pandas for data manipulation
- Celery for task queue
- Pyrebase4 for Firebase
- Openpyxl and XlsxWriter for Excel files
- Requests for HTTP requests
- Redis for caching/message broker

**Recommendation:** Test removing unused packages one by one to ensure the application still works correctly.

## Reinstall package
**Remove all installed package**
- pip freeze > all_packages.txt
- pip uninstall -y -r all_packages.txt
- rm all_packages.txt

**Clear pip cache**
- pip cache purge