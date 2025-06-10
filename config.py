import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Instagram Business API credentials (OAuth method)
    INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID')
    INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET')
    INSTAGRAM_ACCESS_TOKEN = None  # Set via OAuth
    INSTAGRAM_USER_ID = None  # Set via OAuth
    OAUTH_STATE_SECRET = os.getenv('OAUTH_STATE_SECRET', 'your-secure-state-secret')
    
    # WEBHOOK CONFIGURATION (ManyChat Strategy)
    # ========================================
    WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'https://instagram-dm-bot-tk4d.onrender.com')
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', 'your-webhook-verify-token')
    
    # POST MONITORING CONFIGURATION
    # ============================
    MONITOR_ALL_POSTS = False  # Set to True to monitor ALL posts, False to monitor specific posts
    MONITORED_POST_IDS = []  # List of specific post IDs to monitor (when MONITOR_ALL_POSTS is False)
    
    # KEYWORD STRATEGY CONFIGURATION
    # =============================
    # Choose your strategy: 'consent_required' or 'any_keyword'
    KEYWORD_STRATEGY = 'consent_required'  # Options: 'consent_required', 'any_keyword'
    
    # Consent keywords - trigger DIRECT DM sending (when consent_required strategy)
    CONSENT_KEYWORDS = [
        'dm me',
        'send me',
        'message me',
        'dm please',
        'send link',
        'private message',
        'inbox me'
    ]
    
    # Interest keywords - trigger public reply encouraging DM (when consent_required strategy)
    INTEREST_KEYWORDS = [
        'interested',
        'info',
        'details', 
        'link',
        'how',
        'tell me more',
        'want to know',
        'more info'
    ]
    
    # All keywords combined (used when any_keyword strategy is selected)
    KEYWORDS = CONSENT_KEYWORDS + INTEREST_KEYWORDS
    
    # DIRECT DM CONFIGURATION
    # =======================
    ENABLE_DIRECT_DM = True  # Enable ManyChat-style direct DM sending
    
    # DM message template for direct messages
    DM_MESSAGE = """Hi! I saw your comment and here's what you requested: {link}

Let me know if you have any questions! 🙂"""
    
    # Comment reply templates (when DMs fail)
    COMMENT_REPLY_CONSENT = "Hi @{username}! I saw your request. Please DM me and I'll send you the link! 📩"
    COMMENT_REPLY_INTEREST = "Hi @{username}! I saw your interest in '{keyword}'. Please DM me and I'll send you the details! 📩"
    COMMENT_REPLY_ENCOURAGEMENT = "Great question @{username}! DM me '{keyword}' for the full details 📩"
    
    # Default link to send (can be customized)
    DEFAULT_LINK = "https://your-website.com"
    
    # Database file
    DATABASE_FILE = "instagram_bot.db"
    
    # REMOVED: Polling-related settings (no longer needed with webhooks)
    # CHECK_INTERVAL, MAX_POSTS_TO_CHECK, MONITOR_ALL_POSTS, etc.
    
    # FOLLOWER REQUIREMENTS
    # ====================
    MIN_FOLLOWER_COUNT = 0  # Minimum followers to respond to
    ONLY_VERIFIED_ACCOUNTS = False  # Only respond to verified accounts
    
    # DM RATE LIMITING
    # ===============
    MAX_DMS_PER_HOUR = 30  # Instagram rate limit compliance
    MAX_DMS_PER_DAY = 200  # Conservative daily limit
    
    @classmethod
    def load_runtime_config(cls):
        """Load configuration from runtime_config.json if it exists"""
        try:
            if os.path.exists('runtime_config.json'):
                with open('runtime_config.json', 'r') as f:
                    config_data = json.load(f)
                
                # Update class attributes with loaded values
                for key, value in config_data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
                
                # Load webhook-specific settings
                cls.WEBHOOK_BASE_URL = config_data.get('WEBHOOK_BASE_URL', cls.WEBHOOK_BASE_URL)
                cls.WEBHOOK_VERIFY_TOKEN = config_data.get('WEBHOOK_VERIFY_TOKEN', cls.WEBHOOK_VERIFY_TOKEN)
                cls.ENABLE_DIRECT_DM = config_data.get('ENABLE_DIRECT_DM', cls.ENABLE_DIRECT_DM)
                
                # Load Instagram Business API OAuth settings
                cls.INSTAGRAM_APP_ID = config_data.get('INSTAGRAM_APP_ID', cls.INSTAGRAM_APP_ID)
                cls.INSTAGRAM_APP_SECRET = config_data.get('INSTAGRAM_APP_SECRET', cls.INSTAGRAM_APP_SECRET)
                cls.INSTAGRAM_ACCESS_TOKEN = config_data.get('INSTAGRAM_ACCESS_TOKEN', cls.INSTAGRAM_ACCESS_TOKEN)
                cls.INSTAGRAM_USER_ID = config_data.get('INSTAGRAM_USER_ID', cls.INSTAGRAM_USER_ID)
                cls.OAUTH_STATE_SECRET = config_data.get('OAUTH_STATE_SECRET', cls.OAUTH_STATE_SECRET)
                
                # Load keywords
                cls.CONSENT_KEYWORDS = config_data.get('CONSENT_KEYWORDS', cls.CONSENT_KEYWORDS)
                cls.INTEREST_KEYWORDS = config_data.get('INTEREST_KEYWORDS', cls.INTEREST_KEYWORDS)
                cls.KEYWORDS = config_data.get('KEYWORDS', cls.CONSENT_KEYWORDS + cls.INTEREST_KEYWORDS)
                
                # Load post monitoring settings
                cls.MONITOR_ALL_POSTS = config_data.get('MONITOR_ALL_POSTS', cls.MONITOR_ALL_POSTS)
                cls.MONITORED_POST_IDS = config_data.get('MONITORED_POST_IDS', cls.MONITORED_POST_IDS)
                
                # Load keyword strategy
                cls.KEYWORD_STRATEGY = config_data.get('KEYWORD_STRATEGY', getattr(cls, 'KEYWORD_STRATEGY', 'consent_required'))
                
                # Load comment reply templates
                cls.COMMENT_REPLY_CONSENT = config_data.get('COMMENT_REPLY_CONSENT', cls.COMMENT_REPLY_CONSENT)
                cls.COMMENT_REPLY_INTEREST = config_data.get('COMMENT_REPLY_INTEREST', cls.COMMENT_REPLY_INTEREST)
                cls.COMMENT_REPLY_ENCOURAGEMENT = config_data.get('COMMENT_REPLY_ENCOURAGEMENT', cls.COMMENT_REPLY_ENCOURAGEMENT)
                
                print("✅ Runtime configuration loaded successfully")
                return True
            else:
                print("ℹ️ No runtime configuration file found - using defaults")
                return False
                
        except Exception as e:
            print(f"❌ Error loading runtime configuration: {e}")
            return False
    
    @classmethod
    def save_runtime_config(cls):
        """Save current configuration to runtime_config.json"""
        try:
            config_data = {
                # Keywords
                'KEYWORDS': cls.KEYWORDS,
                'CONSENT_KEYWORDS': cls.CONSENT_KEYWORDS,
                'INTEREST_KEYWORDS': cls.INTEREST_KEYWORDS,
                
                # DM Settings
                'DM_MESSAGE': cls.DM_MESSAGE,
                'DEFAULT_LINK': cls.DEFAULT_LINK,
                'ENABLE_DIRECT_DM': cls.ENABLE_DIRECT_DM,
                
                # Comment Reply Templates
                'COMMENT_REPLY_CONSENT': getattr(cls, 'COMMENT_REPLY_CONSENT', "Hi @{username}! I saw your request. Please DM me and I'll send you the link! 📩"),
                'COMMENT_REPLY_INTEREST': getattr(cls, 'COMMENT_REPLY_INTEREST', "Hi @{username}! I saw your interest in '{keyword}'. Please DM me and I'll send you the details! 📩"),
                'COMMENT_REPLY_ENCOURAGEMENT': getattr(cls, 'COMMENT_REPLY_ENCOURAGEMENT', "Great question @{username}! DM me '{keyword}' for the full details 📩"),
                
                # Webhook Settings
                'WEBHOOK_BASE_URL': cls.WEBHOOK_BASE_URL,
                'WEBHOOK_VERIFY_TOKEN': cls.WEBHOOK_VERIFY_TOKEN,
                
                # Instagram Business API OAuth
                'INSTAGRAM_APP_ID': cls.INSTAGRAM_APP_ID,
                'INSTAGRAM_APP_SECRET': cls.INSTAGRAM_APP_SECRET,
                'INSTAGRAM_ACCESS_TOKEN': cls.INSTAGRAM_ACCESS_TOKEN,
                'INSTAGRAM_USER_ID': cls.INSTAGRAM_USER_ID,
                'OAUTH_STATE_SECRET': cls.OAUTH_STATE_SECRET,
                
                # Rate Limiting
                'MAX_DMS_PER_HOUR': cls.MAX_DMS_PER_HOUR,
                'MAX_DMS_PER_DAY': cls.MAX_DMS_PER_DAY,
                'MIN_FOLLOWER_COUNT': cls.MIN_FOLLOWER_COUNT,
                'ONLY_VERIFIED_ACCOUNTS': cls.ONLY_VERIFIED_ACCOUNTS,
                
                # Post Monitoring
                'MONITOR_ALL_POSTS': cls.MONITOR_ALL_POSTS,
                'MONITORED_POST_IDS': cls.MONITORED_POST_IDS,
                
                # Keyword Strategy
                'KEYWORD_STRATEGY': getattr(cls, 'KEYWORD_STRATEGY', 'consent_required')
            }
            
            with open('runtime_config.json', 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print("✅ Runtime configuration saved")
            return True
            
        except Exception as e:
            print(f"❌ Error saving runtime configuration: {e}")
            return False

# Load runtime configuration on import
Config.load_runtime_config() 