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
        """Load runtime configuration changes from JSON file"""
        if os.path.exists(cls.RUNTIME_CONFIG_FILE):
            try:
                with open(cls.RUNTIME_CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                
                if config_data:
                    print(f"📥 Loading runtime configuration...")
                    
                    # Load Instagram session ID
                    if 'INSTAGRAM_SESSION_ID' in config_data:
                        cls.INSTAGRAM_SESSION_ID = config_data['INSTAGRAM_SESSION_ID']
                        if cls.INSTAGRAM_SESSION_ID:
                            print(f"   ✅ Session ID loaded: {cls.INSTAGRAM_SESSION_ID[:20]}...")
                        else:
                            print(f"   ⚠️  No session ID configured")
                    
                    # Load keywords
                    if 'KEYWORDS' in config_data:
                        cls.KEYWORDS = config_data['KEYWORDS']
                        print(f"   ✅ Keywords: {cls.KEYWORDS}")
                    
                    # Load monitoring settings
                    if 'MONITOR_ALL_POSTS' in config_data:
                        cls.MONITOR_ALL_POSTS = config_data['MONITOR_ALL_POSTS']
                        print(f"   ✅ Monitor all posts: {cls.MONITOR_ALL_POSTS}")
                    
                    if 'SPECIFIC_POST_IDS' in config_data:
                        cls.SPECIFIC_POST_IDS = config_data['SPECIFIC_POST_IDS']
                        print(f"   ✅ Specific post IDs: {cls.SPECIFIC_POST_IDS}")
                    
                    # Load filtering criteria
                    if 'REQUIRED_HASHTAGS' in config_data:
                        cls.REQUIRED_HASHTAGS = config_data['REQUIRED_HASHTAGS']
                        print(f"   ✅ Required hashtags: {cls.REQUIRED_HASHTAGS}")
                    
                    if 'REQUIRED_CAPTION_WORDS' in config_data:
                        cls.REQUIRED_CAPTION_WORDS = config_data['REQUIRED_CAPTION_WORDS']
                        print(f"   ✅ Required caption words: {cls.REQUIRED_CAPTION_WORDS}")
                    
                    if 'MAX_POST_AGE_DAYS' in config_data:
                        cls.MAX_POST_AGE_DAYS = config_data['MAX_POST_AGE_DAYS']
                        print(f"   ✅ Max post age: {cls.MAX_POST_AGE_DAYS} days")
                    
                    if 'ONLY_POSTS_WITH_LINKS' in config_data:
                        cls.ONLY_POSTS_WITH_LINKS = config_data['ONLY_POSTS_WITH_LINKS']
                        print(f"   ✅ Only posts with links: {cls.ONLY_POSTS_WITH_LINKS}")
                    
                    # Load DM settings
                    if 'DM_MESSAGE' in config_data:
                        cls.DM_MESSAGE = config_data['DM_MESSAGE']
                        print(f"   ✅ DM message template loaded")
                    
                    if 'DEFAULT_LINK' in config_data:
                        cls.DEFAULT_LINK = config_data['DEFAULT_LINK']
                        print(f"   ✅ Default link: {cls.DEFAULT_LINK}")
                    
                    # Load system settings
                    if 'CHECK_INTERVAL' in config_data:
                        cls.CHECK_INTERVAL = config_data['CHECK_INTERVAL']
                        print(f"   ✅ Check interval: {cls.CHECK_INTERVAL} seconds")
                    
                    if 'MAX_POSTS_TO_CHECK' in config_data:
                        cls.MAX_POSTS_TO_CHECK = config_data['MAX_POSTS_TO_CHECK']
                        print(f"   ✅ Max posts to check: {cls.MAX_POSTS_TO_CHECK}")
                    
                    print(f"📥 Runtime configuration loaded successfully!")
                else:
                    print(f"ℹ️  No runtime configuration found - using defaults")
                
            except Exception as e:
                print(f"❌ Error loading runtime config: {e}")
        else:
            print(f"ℹ️  No runtime config file found, using defaults")
    
    @classmethod
    def save_runtime_config(cls):
        """Save current configuration to JSON file for persistence"""
        runtime_config = {
            'INSTAGRAM_SESSION_ID': cls.INSTAGRAM_SESSION_ID,
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
        }
        
        try:
            with open(cls.RUNTIME_CONFIG_FILE, 'w') as f:
                json.dump(runtime_config, f, indent=2)
            print(f"✅ Configuration saved to {cls.RUNTIME_CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Error saving runtime config: {e}")

# Load runtime configuration on import
Config.load_runtime_config() 