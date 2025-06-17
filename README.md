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

**Production (Cloud):**
- Uses `CHROMEDRIVER_PATH` environment variable
- Set this variable in your production environment
- **Recommended**: Set `SHOW_BROWSER = False` for headless mode

**Example for production:**
```bash
export CHROMEDRIVER_PATH=/path/to/chromedriver
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

### Requirements.txt Cleanup Complete

The requirements.txt file has been cleaned up to include only the packages that are actually used in the codebase:

**Core Packages:**
- **Django and related**: Django, django-crispy-forms, asgiref, sqlparse
- **Celery for background tasks**: celery, celery-progress, django-celery-results, redis, and related dependencies
- **Firebase/Firestore**: firebase-admin, google-cloud-firestore, and authentication packages
- **Web scraping**: selenium, undetected-chromedriver, beautifulsoup4
- **Data processing**: pandas, numpy, openpyxl, XlsxWriter
- **HTTP requests**: requests and related packages
- **Utilities**: lxml, python-dateutil, pytz, soupsieve

**Removed Unused Packages:**
All packages that were not found in the codebase imports have been removed, including:
- arrow, blessed, trio, progress, gspread, oauth2client, pycryptodome, xlrd, xlwt, and many others

This cleanup reduces the number of dependencies from 89 to approximately 35 packages, making the project lighter and easier to maintain.

## Reinstall package
**Remove all installed package**
- pip freeze > all_packages.txt
- pip uninstall -y -r all_packages.txt
- rm all_packages.txt

**Clear pip cache**
- pip cache purge