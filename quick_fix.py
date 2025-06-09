#!/usr/bin/env python3
"""
Quick fix for configuration issues
"""
import json
import os

def fix_configuration():
    """Fix the configuration issues"""
    print("🔧 Fixing Instagram Bot Configuration...")
    
    # Create the runtime configuration
    runtime_config = {
        'KEYWORDS': ['dm me'],
        'MONITOR_ALL_POSTS': False,
        'SPECIFIC_POST_IDS': ['DKpPaxHJQkg'],  # Your monitored post
        'REQUIRED_HASHTAGS': [],
        'REQUIRED_CAPTION_WORDS': [],
        'MAX_POST_AGE_DAYS': 7,
        'ONLY_POSTS_WITH_LINKS': False,
        'DM_MESSAGE': """Hi! Thanks for your interest! 

Here's the link you requested: {link}

Let me know if you have any questions!""",
        'DEFAULT_LINK': "https://your-website.com",  # ⚠️ CHANGE THIS TO YOUR ACTUAL LINK!
        'CHECK_INTERVAL': 30,
        'MAX_POSTS_TO_CHECK': 5,
        'INSTAGRAM_SESSION_ID': None  # Will be set through web interface
    }
    
    # Save the configuration
    try:
        with open('runtime_config.json', 'w') as f:
            json.dump(runtime_config, f, indent=2)
        print("✅ Configuration saved to runtime_config.json")
        
        print("\n📋 Configuration Summary:")
        print(f"✅ Keywords: {runtime_config['KEYWORDS']}")
        print(f"✅ Monitored posts: {runtime_config['SPECIFIC_POST_IDS']}")
        print(f"✅ DM message has {link} placeholder: {'✅' if '{link}' in runtime_config['DM_MESSAGE'] else '❌'}")
        print(f"✅ Default link: {runtime_config['DEFAULT_LINK']}")
        print(f"✅ Check interval: {runtime_config['CHECK_INTERVAL']} seconds")
        
        print("\n🚨 IMPORTANT NEXT STEPS:")
        print("1. 🔗 Change DEFAULT_LINK to your actual website/link")
        print("2. 📱 Update your Instagram session ID through the web interface")
        print("3. 🎯 Verify post ID 'DKpPaxHJQkg' is correct for your monitoring")
        print("4. 🚀 Deploy these changes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

if __name__ == "__main__":
    fix_configuration() 