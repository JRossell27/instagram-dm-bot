import time
import logging
from datetime import datetime, timedelta, timezone
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, PleaseWaitFewMinutes
from config import Config
from database import Database
import os
import random
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)

class InstagramBot:
    def __init__(self):
        self.client = Client()
        self.db = Database()
        self.logged_in = False
        self.username = Config.INSTAGRAM_USERNAME
        self.password = Config.INSTAGRAM_PASSWORD
        self.last_login_check = None
        self.login_check_interval = 300  # Only check login status every 5 minutes
        self.last_login_attempt = None
        self.login_retry_delay = 600  # Wait 10 minutes between failed login attempts
        self.session_file = "session.json"
        
        # Configure client for better persistence
        self._configure_client()
        
    def _configure_client(self):
        """Configure client with realistic settings to avoid detection"""
        # Set realistic user agent (mobile app style)
        mobile_user_agents = [
            "Instagram 250.0.0.16.109 Android (29/10; 360dpi; 720x1448; samsung; SM-A205F; a20; exynos7884B; en_US; 380621387)",
            "Instagram 250.0.0.16.109 Android (28/9; 320dpi; 720x1448; samsung; SM-J415F; j4lte; exynos7570; en_US; 380621387)",
            "Instagram 250.0.0.16.109 Android (30/11; 420dpi; 1080x2340; OnePlus; HD1903; OnePlus7T; qcom; en_US; 380621387)"
        ]
        
        # Set device settings to match a real phone
        self.client.set_user_agent(random.choice(mobile_user_agents))
        
        # Set device UUID and other identifiers consistently
        device_settings = {
            "app_version": "250.0.0.16.109",
            "android_version": 29,
            "android_release": "10",
            "dpi": "360dpi",
            "resolution": "720x1448",
            "manufacturer": "samsung",
            "device": "SM-A205F",
            "model": "a20",
            "cpu": "exynos7884B",
            "version_code": "380621387"
        }
        self.client.set_device(device_settings)
        
        # Set realistic delays
        self.client.delay_range = [3, 7]  # Random delay between 3-7 seconds
        
    def _save_session_safely(self):
        """Save session with backup in case of corruption"""
        try:
            # Save to temporary file first
            temp_file = f"{self.session_file}.tmp"
            self.client.dump_settings(temp_file)
            
            # Create backup of existing session
            if os.path.exists(self.session_file):
                backup_file = f"{self.session_file}.backup"
                os.rename(self.session_file, backup_file)
            
            # Move temp file to main session file
            os.rename(temp_file, self.session_file)
            logging.info("✅ Session saved safely")
            
        except Exception as e:
            logging.error(f"Failed to save session: {e}")
    
    def _load_session_safely(self):
        """Load session with fallback to backup if corrupted"""
        session_loaded = False
        
        # Try main session file
        if os.path.exists(self.session_file):
            try:
                self.client.load_settings(self.session_file)
                session_loaded = True
                logging.info("📱 Loaded main session file")
            except Exception as e:
                logging.warning(f"Main session file corrupted: {e}")
                
                # Try backup session file
                backup_file = f"{self.session_file}.backup"
                if os.path.exists(backup_file):
                    try:
                        self.client.load_settings(backup_file)
                        session_loaded = True
                        logging.info("📱 Loaded backup session file")
                        # Copy backup to main
                        os.rename(backup_file, self.session_file)
                    except Exception as backup_error:
                        logging.warning(f"Backup session also corrupted: {backup_error}")
        
        return session_loaded
    
    def login(self):
        """Login to Instagram using session ID with better persistence"""
        try:
            # Check if we've recently failed a login attempt
            if (self.last_login_attempt and 
                (datetime.now() - self.last_login_attempt).total_seconds() < self.login_retry_delay):
                logging.warning(f"Waiting {self.login_retry_delay} seconds between login attempts to avoid rate limiting")
                return False
                
            logging.info("🔐 Attempting to login to Instagram using session ID...")
            
            # Try to load existing session first
            session_loaded = self._load_session_safely()
            
            # Get session ID from config
            session_id = getattr(Config, 'INSTAGRAM_SESSION_ID', None) or os.getenv('INSTAGRAM_SESSION_ID', '').strip()
            
            if not session_id:
                logging.error("❌ No Instagram session ID provided")
                self.last_login_attempt = datetime.now()
                raise Exception("""Instagram session ID required. To get your session ID:

1. Login to Instagram in your browser
2. Press F12 → Application → Cookies → instagram.com  
3. Find 'sessionid' cookie and copy its value
4. Update it in the web interface under Settings → Instagram Login""")
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(2, 5))
            
            # Try session file login first if available
            if session_loaded:
                try:
                    # Test if session is still valid
                    user_info = self.client.account_info()
                    logging.info(f"✅ Successfully resumed session for @{user_info.username}")
                    self.logged_in = True
                    self.last_login_check = datetime.now()
                    return True
                except Exception as session_error:
                    logging.warning(f"⚠️ Saved session expired: {session_error}")
                    # Continue to session ID login
            
            # Fresh login with session ID
            self.client = Client()  # Create fresh client
            self._configure_client()  # Reapply configuration
            
            # Add longer delay for fresh login
            time.sleep(random.uniform(3, 8))
            
            # Login with session ID
            logging.info("🔑 Logging in with session ID...")
            self.client.login_by_sessionid(session_id)
            
            # Verify login worked
            user_info = self.client.account_info()
            logging.info(f"✅ Successfully logged in as @{user_info.username}")
            
            self.logged_in = True
            self.last_login_check = datetime.now()
            
            # Save session for future use
            self._save_session_safely()
            
            return True
                    
        except Exception as e:
            self.logged_in = False
            self.last_login_attempt = datetime.now()
            error_msg = str(e).lower()
            
            # Provide specific error messages
            if "sessionid" in error_msg or "invalid session" in error_msg or "401" in error_msg:
                logging.error("❌ Instagram session ID expired or invalid")
                raise Exception("""Instagram session ID expired or invalid. To get a new session ID:

1. Login to Instagram in your browser manually
2. Press F12 → Application → Cookies → instagram.com
3. Find 'sessionid' cookie and copy its value  
4. Update it in the web interface under Settings → Instagram Login
5. Session IDs typically last 1-3 months""")
            elif "challenge_required" in error_msg:
                logging.error("❌ Instagram challenge required")
                raise Exception("Instagram requires verification. Login manually in browser first to complete any challenges, then get a new session ID.")
            elif "rate_limit" in error_msg or "too many" in error_msg:
                logging.error("❌ Rate limited by Instagram")
                raise Exception("Instagram rate limit reached. Please wait a few hours before trying again.")
            else:
                logging.error(f"❌ Login failed: {e}")
                raise Exception(f"Instagram login failed: {e}")
    
    def should_monitor_post(self, post):
        """Check if a post should be monitored based on filtering criteria"""
        
        # If monitoring all posts is enabled, monitor everything
        if Config.MONITOR_ALL_POSTS:
            return True
        
        try:
            # Get post details
            post_code = post.code  # This is the short code from the URL
            post_caption = post.caption_text if post.caption_text else ""
            post_date = post.taken_at
            
            # Option 2: Check specific post IDs
            if Config.SPECIFIC_POST_IDS:
                if post_code in Config.SPECIFIC_POST_IDS:
                    logging.info(f"Monitoring post {post_code} - matches specific post ID list")
                    return True
            
            # Option 3: Check required hashtags
            if Config.REQUIRED_HASHTAGS:
                caption_lower = post_caption.lower()
                for hashtag in Config.REQUIRED_HASHTAGS:
                    if hashtag.lower() in caption_lower:
                        logging.info(f"Monitoring post {post_code} - contains required hashtag: {hashtag}")
                        return True
            
            # Option 4: Check required caption words
            if Config.REQUIRED_CAPTION_WORDS:
                caption_lower = post_caption.lower()
                for word in Config.REQUIRED_CAPTION_WORDS:
                    if word.lower() in caption_lower:
                        logging.info(f"Monitoring post {post_code} - contains required phrase: {word}")
                        return True
            
            # Option 5: Check post age - fix timezone comparison
            if Config.MAX_POST_AGE_DAYS:
                # Make both datetimes timezone-aware for comparison
                if post_date.tzinfo is None:
                    # If post_date is naive, assume it's UTC
                    post_date = post_date.replace(tzinfo=timezone.utc)
                
                # Create cutoff date as timezone-aware
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=Config.MAX_POST_AGE_DAYS)
                
                if post_date < cutoff_date:
                    logging.debug(f"Skipping post {post_code} - too old ({post_date})")
                    return False
            
            # Option 6: Check if post contains links (if required)
            if Config.ONLY_POSTS_WITH_LINKS:
                # Simple check for common link indicators
                link_indicators = ['http', 'www.', '.com', '.org', '.net', 'link in bio', 'linkinbio']
                caption_lower = post_caption.lower()
                has_link = any(indicator in caption_lower for indicator in link_indicators)
                if not has_link:
                    logging.debug(f"Skipping post {post_code} - no links detected")
                    return False
            
            # If we have specific filtering criteria but none matched, don't monitor
            if (Config.SPECIFIC_POST_IDS or Config.REQUIRED_HASHTAGS or 
                Config.REQUIRED_CAPTION_WORDS):
                logging.debug(f"Skipping post {post_code} - doesn't match filtering criteria")
                return False
            
            # If no specific filtering is set up, monitor by default
            return True
            
        except Exception as e:
            logging.error(f"Error checking post filter criteria: {e}")
            return False
    
    def check_login_status(self):
        """Check if we're still logged in with better session handling"""
        try:
            # Only check status if we haven't checked recently
            if (self.last_login_check and 
                (datetime.now() - self.last_login_check).total_seconds() < self.login_check_interval):
                return self.logged_in
            
            if not self.logged_in:
                logging.info("🔐 Not logged in, attempting login...")
                return self.login()
            
            # Test if session is still valid with a simple API call
            try:
                # Add small delay to avoid hammering the API
                time.sleep(random.uniform(0.5, 1.5))
                
                user_info = self.client.account_info()
                
                if user_info and user_info.pk:
                    logging.info(f"✅ Session still valid for @{user_info.username}")
                    self.last_login_check = datetime.now()
                    self.logged_in = True
                    
                    # Save the session periodically to keep it fresh
                    self._save_session_safely()
                    
                    return True
                else:
                    logging.warning("⚠️ Session check returned invalid user info")
                    self.logged_in = False
                    return self.login()
                    
            except Exception as check_error:
                error_msg = str(check_error).lower()
                
                if ("login_required" in error_msg or "unauthorized" in error_msg or 
                    "401" in error_msg or "session" in error_msg):
                    logging.warning("⚠️ Session expired, attempting fresh login...")
                    self.logged_in = False
                    return self.login()
                elif "rate" in error_msg or "wait" in error_msg or "429" in error_msg:
                    logging.warning("⏳ Rate limited during login check, assuming still logged in")
                    # Don't mark as logged out for rate limits
                    return self.logged_in
                else:
                    logging.error(f"❌ Unexpected error during login check: {check_error}")
                    # For unknown errors, try to re-login
                    self.logged_in = False
                    return self.login()
                    
        except Exception as e:
            logging.error(f"❌ Critical error in check_login_status: {e}")
            self.logged_in = False
            return False
    
    def get_recent_posts(self, limit=None):
        """Get recent posts from the account with better session handling"""
        if not limit:
            limit = Config.MAX_POSTS_TO_CHECK
            
        try:
            # Only do login check if we're not logged in or session seems expired
            if not self.logged_in:
                if not self.login():
                    logging.error("Unable to login")
                    return []
            
            # Add human-like delay before request
            time.sleep(random.uniform(1, 3))
            
            user_id = self.client.user_id_from_username(Config.INSTAGRAM_USERNAME)
            
            # Add another small delay
            time.sleep(random.uniform(0.5, 2))
            
            posts = self.client.user_medias(user_id, limit)
            logging.info(f"📱 Successfully fetched {len(posts)} posts")
            return posts
            
        except Exception as e:
            error_msg = str(e).lower()
            if ("login_required" in error_msg or "unauthorized" in error_msg or "401" in error_msg) and self.logged_in:
                logging.warning("⚠️ Session expired during post fetch, marking as logged out")
                self.logged_in = False
                self.last_login_attempt = datetime.now()
                return []
            elif "rate" in error_msg or "wait" in error_msg or "429" in error_msg:
                logging.warning("⏳ Rate limited while fetching posts - will retry next cycle")
                # Add longer delay for rate limiting
                time.sleep(random.uniform(10, 20))
                return []
            else:
                logging.error(f"❌ Error fetching posts: {e}")
                return []
    
    def check_comment_for_keywords(self, comment_text):
        """Check if comment contains any of the monitored keywords"""
        comment_lower = comment_text.lower()
        logging.debug(f"Checking comment text: '{comment_text}' against keywords: {Config.KEYWORDS}")
        
        for keyword in Config.KEYWORDS:
            if keyword.lower() in comment_lower:
                logging.info(f"Found keyword '{keyword}' in comment: '{comment_text}'")
                return keyword
        return None
    
    def send_dm(self, user_id, username, keyword):
        """Send DM with human-like behavior and better error handling"""
        try:
            message = self.get_dm_message(keyword)
            if not message:
                logging.error(f"❌ No DM message configured for keyword: {keyword}")
                return False
            
            logging.info(f"📤 Sending DM to @{username} with keyword '{keyword}'")
            
            # Add realistic delay before sending DM
            time.sleep(random.uniform(2, 5))
            
            # Send the DM
            thread = self.client.direct_send(message, [user_id])
            
            if thread:
                logging.info(f"✅ DM sent successfully to @{username}")
                
                # Add longer delay after successful DM
                time.sleep(random.uniform(3, 8))
                return True
            else:
                logging.error(f"❌ Failed to send DM to @{username} - no thread returned")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "challenge_required" in error_msg:
                logging.error(f"❌ Challenge required when sending DM to @{username}")
                # Don't mark as logged out, just skip this DM
                return False
            elif "rate" in error_msg or "wait" in error_msg or "429" in error_msg:
                logging.warning(f"⏳ Rate limited when sending DM to @{username}")
                time.sleep(random.uniform(20, 40))  # Longer delay for DM rates
                return False
            elif "login_required" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
                logging.warning(f"⚠️ Session expired when sending DM to @{username}")
                self.logged_in = False
                return False
            elif "block" in error_msg or "spam" in error_msg:
                logging.error(f"❌ Account may be blocked/flagged when sending DM to @{username}")
                return False
            else:
                logging.error(f"❌ Unexpected error sending DM to @{username}: {e}")
                return False
    
    def process_post_comments(self, post):
        """Process comments on a single post with human-like patterns"""
        try:
            logging.info(f"🔍 Fetching comments for post {post.code}...")
            
            # Check login status before fetching comments
            if not self.check_login_status():
                logging.error("Unable to verify login status before fetching comments")
                return
            
            # Add realistic delay before fetching comments
            time.sleep(random.uniform(2, 5))
            
            comments = self.client.media_comments(post.id)
            
            if not comments:
                logging.info(f"💬 No comments found on post {post.code}")
                return
                
            logging.info(f"💬 Found {len(comments)} total comments on post {post.code}")
            
            processed_count = 0
            already_processed_count = 0
            no_keyword_count = 0
            
            for i, comment in enumerate(comments):
                # Add small delay between comment processing to look human
                if i > 0:
                    time.sleep(random.uniform(0.5, 2))
                
                # Skip if already processed - use comment.pk instead of comment.id
                if self.db.is_comment_processed(str(comment.pk)):
                    already_processed_count += 1
                    continue
                
                # Log the comment for debugging
                logging.info(f"🔍 Checking comment from @{comment.user.username}: '{comment.text[:50]}...'")
                
                # Check for keywords
                keyword = self.check_comment_for_keywords(comment.text)
                if keyword:
                    logging.info(f"🎯 KEYWORD MATCH! Found '{keyword}' in comment from @{comment.user.username}")
                    
                    # Mark as processed first to avoid duplicates - use comment.pk
                    self.db.mark_comment_processed(
                        str(comment.pk),
                        str(comment.user.pk),
                        comment.user.username,
                        str(post.id),
                        keyword
                    )
                    
                    # Add delay before sending DM to look more natural
                    time.sleep(random.uniform(3, 8))
                    
                    # Send DM
                    if self.send_dm(comment.user.pk, comment.user.username, keyword):
                        processed_count += 1
                        logging.info(f"✅ Successfully sent DM to @{comment.user.username}")
                    else:
                        logging.error(f"❌ Failed to send DM to @{comment.user.username}")
                    
                    # Add longer delay after DM to avoid rate limiting
                    time.sleep(random.uniform(5, 12))
                else:
                    no_keyword_count += 1
                    logging.debug(f"➖ No keyword match in comment from @{comment.user.username}")
            
            # Summary logging
            logging.info(f"📊 Comment processing summary for post {post.code}:")
            logging.info(f"  - Total comments: {len(comments)}")
            logging.info(f"  - Already processed: {already_processed_count}")
            logging.info(f"  - No keywords found: {no_keyword_count}")
            logging.info(f"  - New DMs sent: {processed_count}")
            
            if processed_count > 0:
                logging.info(f"🎉 Processed {processed_count} new comments on post {post.code}")
                
        except Exception as e:
            error_msg = str(e).lower()
            if "login_required" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
                logging.warning(f"⚠️ Session expired while processing comments for post {post.code}, will retry next cycle")
                self.logged_in = False
            elif "rate" in error_msg or "wait" in error_msg or "429" in error_msg:
                logging.warning(f"⏳ Rate limited while processing comments for post {post.code}")
                time.sleep(random.uniform(15, 30))
            else:
                logging.error(f"❌ Error processing comments for post {post.code}: {e}")
    
    def run_monitoring_cycle(self):
        """Run one cycle of comment monitoring"""
        if not self.logged_in:
            if not self.login():
                return False
        
        try:
            logging.info("Starting comment monitoring cycle...")
            logging.info(f"Current keywords: {Config.KEYWORDS}")
            logging.info(f"Monitored post IDs: {Config.SPECIFIC_POST_IDS}")
            logging.info(f"DM message: {Config.DM_MESSAGE}")
            
            # Get recent posts
            all_posts = self.get_recent_posts()
            if not all_posts:
                logging.warning("No posts found to check")
                return True
            
            # Filter posts based on criteria
            posts_to_monitor = []
            for post in all_posts:
                if self.should_monitor_post(post):
                    posts_to_monitor.append(post)
            
            if not posts_to_monitor:
                logging.info(f"No posts match monitoring criteria out of {len(all_posts)} checked")
                return True
            
            logging.info(f"Monitoring {len(posts_to_monitor)} posts out of {len(all_posts)} recent posts")
            
            # Process each eligible post
            for post in posts_to_monitor:
                self.process_post_comments(post)
                time.sleep(1)  # Small delay between posts
            
            logging.info(f"Completed monitoring cycle for {len(posts_to_monitor)} posts")
            return True
            
        except PleaseWaitFewMinutes:
            logging.warning("Rate limited - waiting before next cycle")
            return True
        except Exception as e:
            logging.error(f"Error in monitoring cycle: {e}")
            return False
    
    def get_stats(self):
        """Get statistics about processed comments and sent DMs"""
        recent_comments = self.db.get_recent_processed_comments(10)
        return {
            'recent_processed': recent_comments,
            'logged_in': self.logged_in,
            'username': Config.INSTAGRAM_USERNAME if self.logged_in else None
        }
    
    def list_recent_posts_for_selection(self):
        """Helper method to show recent posts for manual selection"""
        try:
            posts = self.get_recent_posts(10)  # Get more posts for selection
            
            print("\nYour Recent Posts:")
            print("="*50)
            
            for i, post in enumerate(posts, 1):
                post_url = f"https://www.instagram.com/p/{post.code}/"
                caption_preview = (post.caption_text[:50] + "...") if post.caption_text else "No caption"
                print(f"{i}. Post ID: {post.code}")
                print(f"   URL: {post_url}")
                print(f"   Caption: {caption_preview}")
                print(f"   Date: {post.taken_at}")
                print()
                
        except Exception as e:
            logging.error(f"Error listing posts: {e}")
    
    def get_dm_message(self, keyword):
        """Get the appropriate DM message for a keyword"""
        try:
            # Try to get custom messages from config first
            if hasattr(Config, 'DM_MESSAGES') and isinstance(Config.DM_MESSAGES, dict):
                if keyword in Config.DM_MESSAGES:
                    return Config.DM_MESSAGES[keyword]
            
            # Fall back to default message
            if hasattr(Config, 'DM_MESSAGE') and Config.DM_MESSAGE:
                return Config.DM_MESSAGE.format(link=getattr(Config, 'DEFAULT_LINK', ''))
            
            # Ultimate fallback
            return f"Hi! I saw your comment '{keyword}'. Here's the link you requested: {getattr(Config, 'DEFAULT_LINK', 'https://example.com')}"
            
        except Exception as e:
            logging.error(f"Error getting DM message for keyword '{keyword}': {e}")
            return None 