import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Instagram credentials
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    
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
    
    # Check interval in minutes
    CHECK_INTERVAL = 5
    
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