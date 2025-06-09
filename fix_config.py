#!/usr/bin/env python3

"""
Fix configuration script to reset keywords and save proper runtime config
"""

from config import Config
import json
import os

def fix_configuration():
    """Fix and save the configuration"""
    print("🔧 Fixing configuration...")
    
    # Ensure keywords are set
    if not Config.KEYWORDS:
        print("❌ Keywords are empty, resetting to defaults...")
        Config.KEYWORDS = [
            'dm me',
            'send link', 
            'info',
            'details',
            'interested'
        ]
    
    # Set sensible defaults
    Config.MONITOR_ALL_POSTS = False
    Config.SPECIFIC_POST_IDS = ['DKpPaxHJQkg']  # Your monitored post
    Config.CHECK_INTERVAL = 30  # 30 seconds
    Config.MAX_POSTS_TO_CHECK = 5
    
    # Ensure DM message has the link placeholder
    if '{link}' not in Config.DM_MESSAGE:
        Config.DM_MESSAGE = """Hi! Thanks for your interest! 

Here's the link you requested: {link}

Let me know if you have any questions!"""
    
    # Save the configuration
    Config.save_runtime_config()
    
    print("✅ Configuration fixed and saved!")
    print(f"✅ Keywords: {Config.KEYWORDS}")
    print(f"✅ Monitored posts: {Config.SPECIFIC_POST_IDS}")
    print(f"✅ Check interval: {Config.CHECK_INTERVAL} seconds")

if __name__ == "__main__":
    fix_configuration() 