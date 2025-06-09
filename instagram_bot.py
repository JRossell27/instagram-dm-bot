import time
import logging
from datetime import datetime, timedelta
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, PleaseWaitFewMinutes
from config import Config
from database import Database
import os

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
        
    def login(self):
        """Login to Instagram with backup code support"""
        try:
            logging.info("Attempting to login to Instagram...")
            
            # Try to load existing session first
            session_file = "session.json"
            if os.path.exists(session_file):
                try:
                    self.client.load_settings(session_file)
                    self.client.login(self.username, self.password)
                    logging.info("Logged in using saved session")
                    self.logged_in = True
                    return True
                except Exception as e:
                    logging.warning(f"Failed to use saved session: {e}")
                    # Continue with fresh login
            
            # Get backup code from environment
            backup_code = os.getenv('INSTAGRAM_2FA_CODE', '').replace(' ', '')
            
            if backup_code:
                # Login with backup code
                logging.info("Using provided backup code for login...")
                self.client.login(self.username, self.password, verification_code=backup_code)
                logging.info("Successfully logged in using backup code")
            else:
                # Login without 2FA
                logging.info("No backup code provided, attempting login without 2FA...")
                self.client.login(self.username, self.password)
                logging.info("Successfully logged in without 2FA")
            
            self.logged_in = True
            
            # Save session for future use
            self.client.dump_settings(session_file)
            logging.info("Session saved for future logins")
            
            return True
                    
        except Exception as e:
            self.logged_in = False
            error_msg = str(e).lower()
            
            # Provide specific error messages
            if "security code" in error_msg or "check the security code" in error_msg:
                logging.error("Instagram backup code rejected")
                raise Exception("""Instagram backup code rejected. This usually means:
1. The backup code has already been used (each can only be used once)
2. The backup code is invalid or expired
3. Instagram is rejecting automated login attempts

Solutions:
- Generate NEW backup codes from Instagram app: Settings → Security → Two-Factor Authentication → Recovery Codes
- Use a fresh, unused backup code
- Make sure to remove spaces from the code""")
            elif "two_factor_required" in error_msg or "two-factor authentication required" in error_msg:
                logging.error("2FA required but no backup code provided")
                raise Exception("Instagram 2FA required. Please add INSTAGRAM_2FA_CODE environment variable with your backup code (without spaces).")
            elif "challenge_required" in error_msg:
                logging.error("Instagram challenge required")
                raise Exception("Instagram requires verification. Try logging in manually first to complete any challenges.")
            elif "invalid_user" in error_msg or "bad_password" in error_msg:
                logging.error("Invalid credentials")
                raise Exception("Invalid Instagram username or password. Please check credentials.")
            elif "rate_limit" in error_msg or "too many" in error_msg:
                logging.error("Rate limited by Instagram")
                raise Exception("Instagram rate limit reached. Please wait a few hours before trying again.")
            else:
                logging.error(f"Login failed: {e}")
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
            
            # Option 5: Check post age
            if Config.MAX_POST_AGE_DAYS:
                cutoff_date = datetime.now() - timedelta(days=Config.MAX_POST_AGE_DAYS)
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
    
    def get_recent_posts(self, limit=None):
        """Get recent posts from the account"""
        if not limit:
            limit = Config.MAX_POSTS_TO_CHECK
            
        try:
            user_id = self.client.user_id_from_username(Config.INSTAGRAM_USERNAME)
            posts = self.client.user_medias(user_id, limit)
            return posts
        except Exception as e:
            logging.error(f"Error fetching posts: {e}")
            return []
    
    def check_comment_for_keywords(self, comment_text):
        """Check if comment contains any of the monitored keywords"""
        comment_lower = comment_text.lower()
        for keyword in Config.KEYWORDS:
            if keyword.lower() in comment_lower:
                return keyword
        return None
    
    def send_dm(self, user_id, username, keyword):
        """Send DM to user with the configured message and link"""
        try:
            message = Config.DM_MESSAGE.format(link=Config.DEFAULT_LINK)
            
            # Send the DM
            self.client.direct_send(message, [user_id])
            
            # Log the sent DM
            self.db.log_sent_dm(user_id, username, message)
            
            logging.info(f"DM sent to @{username} (keyword: {keyword})")
            return True
            
        except Exception as e:
            logging.error(f"Error sending DM to @{username}: {e}")
            return False
    
    def process_post_comments(self, post):
        """Process comments on a single post"""
        try:
            comments = self.client.media_comments(post.id)
            processed_count = 0
            
            for comment in comments:
                # Skip if already processed
                if self.db.is_comment_processed(str(comment.id)):
                    continue
                
                # Check for keywords
                keyword = self.check_comment_for_keywords(comment.text)
                if keyword:
                    # Mark as processed first to avoid duplicates
                    self.db.mark_comment_processed(
                        str(comment.id),
                        str(comment.user.pk),
                        comment.user.username,
                        str(post.id),
                        keyword
                    )
                    
                    # Send DM
                    if self.send_dm(comment.user.pk, comment.user.username, keyword):
                        processed_count += 1
                    
                    # Add delay to avoid rate limiting
                    time.sleep(2)
            
            if processed_count > 0:
                logging.info(f"Processed {processed_count} new comments on post {post.code}")
                
        except Exception as e:
            logging.error(f"Error processing comments for post {post.code}: {e}")
    
    def run_monitoring_cycle(self):
        """Run one cycle of comment monitoring"""
        if not self.logged_in:
            if not self.login():
                return False
        
        try:
            logging.info("Starting comment monitoring cycle...")
            
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