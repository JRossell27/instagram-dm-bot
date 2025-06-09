#!/usr/bin/env python3
"""
Instagram Session Extractor
This script helps you extract your Instagram session ID from browser cookies
to bypass 2FA authentication issues.
"""

import json
import os
from pathlib import Path

def extract_chrome_session():
    """Extract Instagram session from Chrome cookies"""
    print("🔍 Looking for Chrome Instagram cookies...")
    
    # Chrome cookie paths for different OS
    chrome_paths = [
        # macOS
        os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
        # Windows
        os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cookies"),
        # Linux
        os.path.expanduser("~/.config/google-chrome/Default/Cookies")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"📁 Found Chrome cookies at: {path}")
            print("\n⚠️  Chrome stores cookies in SQLite format.")
            print("You'll need to:")
            print("1. Install a browser extension like 'Cookie Editor'")
            print("2. Go to instagram.com while logged in")
            print("3. Find the 'sessionid' cookie")
            print("4. Copy its value")
            return True
    
    print("❌ Chrome cookies not found")
    return False

def manual_session_instructions():
    """Provide manual instructions for session extraction"""
    print("\n" + "="*60)
    print("📱 MANUAL SESSION EXTRACTION INSTRUCTIONS")
    print("="*60)
    
    print("\n🌐 Method 1: Browser Developer Tools")
    print("1. Open Instagram in your browser and login normally")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to 'Application' tab → 'Cookies' → 'https://www.instagram.com'")
    print("4. Find 'sessionid' cookie and copy its value")
    print("5. The value looks like: '12345%3AAbCdEf...'")
    
    print("\n🔧 Method 2: Browser Extension")
    print("1. Install 'Cookie Editor' extension")
    print("2. Go to instagram.com while logged in")
    print("3. Click the extension icon")
    print("4. Find 'sessionid' and copy its value")
    
    print("\n🤖 Method 3: Use this extracted session")
    print("Once you have the sessionid:")
    print("1. Add it as environment variable: INSTAGRAM_SESSION_ID")
    print("2. Remove INSTAGRAM_2FA_CODE variable")
    print("3. The bot will use session login instead")

def create_session_login_method():
    """Create updated login method for session ID"""
    session_code = '''
    def login_with_session(self):
        """Login using extracted session ID"""
        session_id = os.getenv('INSTAGRAM_SESSION_ID', '').strip()
        
        if session_id:
            logging.info("Attempting login with provided session ID...")
            try:
                self.client.login_by_sessionid(session_id)
                logging.info("Successfully logged in using session ID")
                self.logged_in = True
                return True
            except Exception as e:
                logging.error(f"Session ID login failed: {e}")
                raise Exception("Session ID login failed. Please extract a fresh session ID.")
        else:
            raise Exception("No session ID provided. Please set INSTAGRAM_SESSION_ID environment variable.")
    '''
    
    print("\n" + "="*60)
    print("🔄 UPDATED LOGIN METHOD CODE")
    print("="*60)
    print(session_code)

if __name__ == "__main__":
    print("🚀 Instagram Session Extractor")
    print("="*50)
    
    # Try to find browser cookies
    found_chrome = extract_chrome_session()
    
    # Provide manual instructions
    manual_session_instructions()
    
    # Show code update
    create_session_login_method()
    
    print("\n" + "="*60)
    print("💡 WHY THIS WORKS:")
    print("- Session IDs bypass 2FA completely")
    print("- Instagram trusts existing browser sessions")
    print("- No automated login = no bot detection")
    print("- Sessions last for weeks/months")
    print("="*60) 