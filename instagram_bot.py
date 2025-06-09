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
        """Login to Instagram with 2FA support"""
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
            
            # Fresh login attempt with 2FA support
            try:
                # First try login without 2FA
                self.client.login(self.username, self.password)
                logging.info("Successfully logged in to Instagram without 2FA")
                self.logged_in = True
                
                # Save session for future use
                self.client.dump_settings(session_file)
                logging.info("Session saved for future logins")
                
                return True
                
            except Exception as login_error:
                error_msg = str(login_error).lower()
                
                # Check if 2FA is required
                if "two_factor_required" in error_msg or "two-factor authentication required" in error_msg:
                    logging.info("2FA required, attempting backup code authentication...")
                    
                    # Get backup code from environment
                    backup_code = os.getenv('INSTAGRAM_2FA_CODE', '').replace(' ', '')
                    
                    if not backup_code:
                        logging.error("2FA required but no backup code provided")
                        raise Exception("Instagram 2FA required. Please add INSTAGRAM_2FA_CODE environment variable with your backup code (without spaces).")
                    
                    try:
                        # Use the two_factor_login method for backup codes
                        # This is different from the verification_code parameter
                        from instagrapi.exceptions import TwoFactorRequired
                        
                        # The TwoFactorRequired exception should contain the two_factor_identifier
                        # We need to handle this properly
                        
                        # Try using the backup code as a regular verification code first
                        try:
                            self.client.login(self.username, self.password, verification_code=backup_code)
                            logging.info("Successfully logged in using backup code as verification code")
                        except Exception as backup_error:
                            logging.info(f"Backup code as verification failed: {backup_error}")
                            
                            # If that fails, try the two_factor_login endpoint directly
                            # This requires manual handling of the 2FA flow
                            logging.info("Attempting manual 2FA login with backup code...")
                            
                            # Perform initial login to get 2FA challenge
                            try:
                                self.client.login(self.username, self.password)
                            except TwoFactorRequired as tfa_error:
                                # Extract two_factor_identifier from the exception
                                two_factor_info = tfa_error.response.json()
                                two_factor_identifier = two_factor_info.get('two_factor_info', {}).get('two_factor_identifier')
                                
                                if two_factor_identifier:
                                    logging.info("Got 2FA identifier, submitting backup code...")
                                    
                                    # Submit backup code using the two_factor_login endpoint
                                    login_data = {
                                        'verification_code': backup_code,
                                        'two_factor_identifier': two_factor_identifier,
                                        'username': self.username,
                                        'trust_this_device': '1'
                                    }
                                    
                                    response = self.client.private_request('accounts/two_factor_login/', login_data, login=True)
                                    
                                    if response.get('logged_in_user'):
                                        logging.info("Successfully logged in using backup code via two_factor_login")
                                        self.logged_in = True
                                        
                                        # Save session for future use
                                        self.client.dump_settings(session_file)
                                        logging.info("Session saved for future logins")
                                        
                                        return True
                                    else:
                                        raise Exception("Backup code authentication failed")
                                else:
                                    raise Exception("Could not get 2FA identifier from Instagram")
                            except Exception as manual_error:
                                logging.error(f"Manual 2FA login failed: {manual_error}")
                                raise Exception(f"Backup code authentication failed: {manual_error}")
                        
                        self.logged_in = True
                        
                        # Save session for future use
                        self.client.dump_settings(session_file)
                        logging.info("Session saved for future logins")
                        
                        return True
                        
                    except Exception as backup_error:
                        logging.error(f"Backup code authentication failed: {backup_error}")
                        backup_error_msg = str(backup_error).lower()
                        
                        if "security code" in backup_error_msg or "check the security code" in backup_error_msg:
                            raise Exception("Instagram backup code is invalid or expired. Please generate a new backup code from Instagram settings and update INSTAGRAM_2FA_CODE.")
                        elif "invalid" in backup_error_msg:
                            raise Exception("Instagram backup code is invalid. Please check the code and try again.")
                        else:
                            raise Exception(f"Instagram backup code authentication failed: {backup_error}")
                            
                elif "challenge_required" in error_msg:
                    logging.error("Instagram challenge required - account may be flagged")
                    raise Exception("Instagram requires verification. Try logging in manually first.")
                elif "invalid_user" in error_msg or "bad_password" in error_msg:
                    logging.error("Invalid username or password")
                    raise Exception("Invalid Instagram username or password. Please check credentials.")
                elif "rate_limit" in error_msg:
                    logging.error("Rate limited by Instagram")
                    raise Exception("Instagram rate limit reached. Please try again later.")
                else:
                    logging.error(f"Login failed: {login_error}")
                    raise Exception(f"Instagram login failed: {login_error}")
                    
        except Exception as e:
            self.logged_in = False
            logging.error(f"Instagram login error: {e}")
            raise e
    
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