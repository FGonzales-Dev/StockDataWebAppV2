#!/usr/bin/env python3
"""
Scraping Mode Manager
====================

Simple script to switch between different scraping modes:
- direct: Run scraping synchronously (user waits, no Redis needed)
- background: Use Redis/Celery for background tasks
- auto: Automatically detect what's available

Usage:
    python manage_scraping.py status          # Check current mode
    python manage_scraping.py direct          # Switch to direct mode
    python manage_scraping.py background      # Switch to background mode  
    python manage_scraping.py auto            # Switch to auto mode
"""

import sys
import os

def read_config():
    """Read current scraping configuration"""
    try:
        with open('scraping_mode_config.py', 'r') as f:
            content = f.read()
            
        # Extract current mode
        for line in content.split('\n'):
            if line.strip().startswith('SCRAPING_MODE = '):
                mode = line.split('=')[1].strip().strip("'\"").split('#')[0].strip()
                return mode
        return 'auto'  # default
    except FileNotFoundError:
        return 'auto'

def write_config(mode):
    """Update scraping configuration"""
    config_content = f"""# Scraping Mode Configuration
# =========================

# Set this to control scraping behavior:
# - 'auto': Automatically detect Redis/Celery availability (recommended)
# - 'direct': Always use direct/synchronous scraping
# - 'background': Always try to use Redis/Celery (will fail if not available)

SCRAPING_MODE = '{mode}'

# Redis/Celery Configuration (used when available)
USE_REDIS_WHEN_AVAILABLE = True
REDIS_FALLBACK_TO_DIRECT = True  # If Redis fails, fall back to direct

# Direct Mode Settings
DIRECT_MODE_SHOW_PROGRESS = True  # Show immediate results in direct mode
DIRECT_MODE_TIMEOUT = 300  # 5 minutes timeout for direct scraping
"""
    
    with open('scraping_mode_config.py', 'w') as f:
        f.write(config_content)

def show_status():
    """Show current configuration status"""
    current_mode = read_config()
    
    print(f"🔧 Current Scraping Mode: {current_mode}")
    print()
    
    if current_mode == 'direct':
        print("📋 Direct Mode:")
        print("   ✅ Scraping runs immediately (synchronous)")
        print("   ✅ User waits for results")
        print("   ✅ No Redis/Celery required")
        print("   ❌ Slower user experience")
        
    elif current_mode == 'background':
        print("📋 Background Mode:")
        print("   ✅ Scraping runs in background (asynchronous)")
        print("   ✅ Fast user experience")
        print("   ❌ Requires Redis and Celery")
        print("   ❌ More complex setup")
        
    elif current_mode == 'auto':
        print("📋 Auto Mode:")
        print("   ✅ Automatically detects Redis/Celery")
        print("   ✅ Uses background if available, direct if not")
        print("   ✅ Best of both worlds")
        print("   ✅ Recommended for production")

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_scraping.py [status|direct|background|auto]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_status()
        
    elif command in ['direct', 'background', 'auto']:
        old_mode = read_config()
        write_config(command)
        print(f"✅ Scraping mode changed from '{old_mode}' to '{command}'")
        print("🔄 Restart your Django server for changes to take effect")
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: status, direct, background, auto")
        sys.exit(1)

if __name__ == "__main__":
    main() 