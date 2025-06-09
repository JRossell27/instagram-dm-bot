import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Instagram credentials
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    INSTAGRAM_SESSION_ID = None  # Will be managed through web interface
    
    # Keywords to monitor (can be modified)
    KEYWORDS = [
        'dm me',
        'send link',
        'info',
        'details',
        'interested'
    ]
    
    # DM message template
    DM_MESSAGE = """Hi! Thanks for your interest! 

Here's the link you requested: {link}

Let me know if you have any questions!"""
    
    # Default link to send (can be customized)
    DEFAULT_LINK = "https://your-website.com"
    
    # Database file
    DATABASE_FILE = "instagram_bot.db"
    
    # Check interval in seconds
    CHECK_INTERVAL = 30
    
    # Maximum posts to check per run
    MAX_POSTS_TO_CHECK = 5
    
    # POST FILTERING OPTIONS
    # ===================
    
    # Option 1: Monitor ALL posts (set to True to monitor all posts)
    MONITOR_ALL_POSTS = False
    
    # Option 2: Specific post IDs to monitor (get these from Instagram URLs)
    # Example: from URL https://www.instagram.com/p/ABC123DEF/ use "ABC123DEF"
    SPECIFIC_POST_IDS = [
        # "ABC123DEF",  # Replace with your actual post IDs
        # "XYZ789GHI",
    ]
    
    # Option 3: Only monitor posts with specific hashtags in caption
    REQUIRED_HASHTAGS = [
        # "#dmbot",      # Only monitor posts with this hashtag
        # "#automate",   # Add multiple hashtags as needed
    ]
    
    # Option 4: Only monitor posts with specific words in caption
    REQUIRED_CAPTION_WORDS = [
        # "link in bio",     # Only monitor posts mentioning this
        # "dm for details",  # Add phrases to look for
    ]
    
    # Option 5: Only monitor posts newer than X days
    MAX_POST_AGE_DAYS = 7  # Set to None to disable age filtering
    
    # Option 6: Only monitor posts that contain links in bio/caption
    ONLY_POSTS_WITH_LINKS = False

    # Runtime configuration file
    RUNTIME_CONFIG_FILE = "runtime_config.json"
    
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
                'KEYWORDS': cls.KEYWORDS,
                'MONITOR_ALL_POSTS': cls.MONITOR_ALL_POSTS,
                'SPECIFIC_POST_IDS': cls.SPECIFIC_POST_IDS,
                'REQUIRED_HASHTAGS': cls.REQUIRED_HASHTAGS,
                'REQUIRED_CAPTION_WORDS': cls.REQUIRED_CAPTION_WORDS,
                'MAX_POST_AGE_DAYS': cls.MAX_POST_AGE_DAYS,
                'ONLY_POSTS_WITH_LINKS': cls.ONLY_POSTS_WITH_LINKS,
                'DM_MESSAGE': cls.DM_MESSAGE,
                'DEFAULT_LINK': cls.DEFAULT_LINK,
                'CHECK_INTERVAL': cls.CHECK_INTERVAL,
                'MAX_POSTS_TO_CHECK': cls.MAX_POSTS_TO_CHECK,
                'INSTAGRAM_SESSION_ID': cls.INSTAGRAM_SESSION_ID
            }
            
            with open('runtime_config.json', 'w') as f:
                json.dump(config_data, f, indent=2)
                
            print("✅ Runtime configuration saved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving runtime configuration: {e}")
            return False

# Load runtime configuration on import
Config.load_runtime_config() 