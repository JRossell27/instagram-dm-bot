import time
import logging
import requests
import json
from datetime import datetime, timedelta, timezone
from config import Config
from database import Database
import os
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)

class InstagramBusinessBot:
    def __init__(self):
        self.db = Database()
        self.logged_in = False
        self.access_token = Config.INSTAGRAM_ACCESS_TOKEN
        self.user_id = Config.INSTAGRAM_USER_ID
        self.last_login_check = None
        self.login_check_interval = 300  # Check every 5 minutes
        
        # Encouragement messages for comments
        self.dm_encouragement_messages = [
            "Great question! DM us '{keyword}' for the full details 📩",
            "Interested? Send us a DM with '{keyword}' and we'll share the link! 💌",
            "Perfect! DM '{keyword}' and we'll send you all the info privately 🔗",
            "Thanks for asking! Send '{keyword}' in a DM and we'll hook you up! ✨",
            "Love the interest! DM us '{keyword}' for exclusive access 🚀"
        ]
        
    def login(self):
        """Verify Instagram Business API authentication"""
        try:
            if not self.access_token or not self.user_id:
                logging.error("❌ Instagram Business API credentials not configured")
                raise Exception("Instagram Business App not configured. Please authenticate via OAuth first.")
            
            # Test the access token by making a simple API call
            test_url = f"https://graph.instagram.com/v21.0/{self.user_id}"
            params = {
                'fields': 'id,username,account_type,media_count',
                'access_token': self.access_token
            }
            
            response = requests.get(test_url, params=params)
            
            if response.status_code == 200:
                user_info = response.json()
                username = user_info.get('username', 'Unknown')
                account_type = user_info.get('account_type', 'Unknown')
                media_count = user_info.get('media_count', 0)
                
                logging.info(f"✅ Instagram Business API authenticated - @{username} ({account_type}) - {media_count} posts")
                self.logged_in = True
                self.last_login_check = datetime.now()
                return True
            else:
                error_data = response.json() if response.text else {}
                logging.error(f"❌ API authentication failed: {response.status_code} - {error_data}")
                self.logged_in = False
                raise Exception(f"Instagram API authentication failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
                
        except Exception as e:
            self.logged_in = False
            logging.error(f"❌ Instagram Business API login failed: {e}")
            raise e
            
    def check_login_status(self):
        """Periodically verify API access is still valid"""
        try:
            if not self.last_login_check or (datetime.now() - self.last_login_check).total_seconds() > self.login_check_interval:
                return self.login()
            return self.logged_in
        except Exception as e:
            logging.error(f"Login status check failed: {e}")
            return False
    
    def get_recent_posts(self, limit=10):
        """Get recent posts using Instagram Business API"""
        try:
            if not self.check_login_status():
                return []
            
            # Get user's media
            url = f"https://graph.instagram.com/v21.0/{self.user_id}/media"
            params = {
                'fields': 'id,caption,media_type,media_url,permalink,timestamp,comments_count,like_count',
                'limit': limit or Config.MAX_POSTS_TO_CHECK,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                for media in data.get('data', []):
                    # Convert to a format similar to what we had before
                    post = {
                        'id': media['id'],
                        'caption': media.get('caption', ''),
                        'media_type': media.get('media_type', ''),
                        'url': media.get('permalink', ''),
                        'timestamp': media.get('timestamp', ''),
                        'comments_count': media.get('comments_count', 0),
                        'like_count': media.get('like_count', 0)
                    }
                    posts.append(post)
                
                logging.info(f"📱 Retrieved {len(posts)} recent posts from Business API")
                return posts
            else:
                logging.error(f"Failed to get posts: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Error getting recent posts: {e}")
            return []
    
    def should_monitor_post(self, post):
        """Check if we should monitor this post based on settings"""
        try:
            # If monitoring all posts
            if Config.MONITOR_ALL_POSTS:
                return True
                
            # Check specific post IDs
            if Config.SPECIFIC_POST_IDS and post['id'] in Config.SPECIFIC_POST_IDS:
                return True
                
            # Check required hashtags
            if Config.REQUIRED_HASHTAGS:
                caption = post.get('caption', '').lower()
                for hashtag in Config.REQUIRED_HASHTAGS:
                    if hashtag.lower() in caption:
                        return True
                        
            # Check required caption words
            if Config.REQUIRED_CAPTION_WORDS:
                caption = post.get('caption', '').lower()
                for word in Config.REQUIRED_CAPTION_WORDS:
                    if word.lower() in caption:
                        return True
                        
            # Check post age
            if Config.MAX_POST_AGE_DAYS:
                try:
                    post_time = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    age_days = (datetime.now(timezone.utc) - post_time).days
                    if age_days > Config.MAX_POST_AGE_DAYS:
                        return False
                except:
                    pass  # If can't parse date, assume it's recent
                    
            return len(Config.SPECIFIC_POST_IDS) == 0  # Default behavior
            
        except Exception as e:
            logging.error(f"Error checking if should monitor post: {e}")
            return False
    
    def get_post_comments(self, post_id, limit=50):
        """Get comments on a specific post"""
        try:
            url = f"https://graph.instagram.com/v21.0/{post_id}/comments"
            params = {
                'fields': 'id,text,username,timestamp,from',
                'limit': limit,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                comments = []
                
                for comment in data.get('data', []):
                    comment_data = {
                        'id': comment['id'],
                        'text': comment.get('text', ''),
                        'username': comment.get('username', comment.get('from', {}).get('username', 'unknown')),
                        'user_id': comment.get('from', {}).get('id', ''),
                        'timestamp': comment.get('timestamp', '')
                    }
                    comments.append(comment_data)
                
                return comments
            else:
                logging.error(f"Failed to get comments for post {post_id}: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error getting comments for post {post_id}: {e}")
            return []
    
    def check_comment_for_keywords(self, comment_text):
        """Check if comment contains any of our keywords"""
        comment_lower = comment_text.lower()
        for keyword in Config.KEYWORDS:
            if keyword.lower() in comment_lower:
                return keyword
        return None
    
    def reply_to_comment(self, comment_id, message):
        """Reply to a comment publicly"""
        try:
            url = f"https://graph.instagram.com/v21.0/{comment_id}/replies"
            data = {
                'message': message,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logging.info(f"✅ Successfully replied to comment {comment_id}")
                return True
            else:
                logging.error(f"Failed to reply to comment {comment_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error replying to comment {comment_id}: {e}")
            return False
    
    def get_dm_encouragement_message(self, keyword):
        """Get a random encouragement message for DMs"""
        template = random.choice(self.dm_encouragement_messages)
        return template.format(keyword=keyword.upper())
    
    def process_post_comments(self, post):
        """Process comments on a post and reply encouraging DMs"""
        try:
            post_id = post['id']
            logging.info(f"🔍 Processing comments for post {post_id}")
            
            comments = self.get_post_comments(post_id)
            processed_count = 0
            
            for comment in comments:
                # Check if we've already processed this comment
                if self.db.is_comment_processed(comment['id']):
                    continue
                
                # Check if comment contains keywords
                matched_keyword = self.check_comment_for_keywords(comment['text'])
                
                if matched_keyword:
                    logging.info(f"🎯 Found keyword '{matched_keyword}' in comment by @{comment['username']}")
                    
                    # Generate encouragement message
                    reply_message = self.get_dm_encouragement_message(matched_keyword)
                    
                    # Reply to the comment publicly
                    if self.reply_to_comment(comment['id'], reply_message):
                        # Mark comment as processed
                        self.db.add_processed_comment(
                            comment_id=comment['id'],
                            post_id=post_id,
                            username=comment['username'],
                            user_id=comment['user_id'],
                            comment_text=comment['text'],
                            keyword=matched_keyword,
                            action_taken='replied_encouraging_dm'
                        )
                        processed_count += 1
                        
                        # Add delay to avoid rate limits
                        time.sleep(random.uniform(2, 5))
                    else:
                        logging.error(f"Failed to reply to comment by @{comment['username']}")
                else:
                    # Mark as seen but no action taken
                    self.db.add_processed_comment(
                        comment_id=comment['id'],
                        post_id=post_id,
                        username=comment['username'],
                        user_id=comment['user_id'],
                        comment_text=comment['text'],
                        keyword=None,
                        action_taken='no_keyword_match'
                    )
            
            logging.info(f"📊 Processed {len(comments)} comments, replied to {processed_count}")
            return processed_count > 0
            
        except Exception as e:
            logging.error(f"Error processing comments for post {post['id']}: {e}")
            return False
    
    def get_incoming_messages(self):
        """Get incoming DMs (Instagram Business API limitation: can only see messages initiated by users)"""
        try:
            # Note: Instagram Business API has limitations for DMs
            # We can only receive/respond to messages that users send us first
            # This is a placeholder for when Instagram expands these capabilities
            
            url = f"https://graph.instagram.com/v21.0/{self.user_id}/conversations"
            params = {
                'fields': 'id,participants,updated_time,message_count',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('data', [])
                logging.info(f"📩 Found {len(conversations)} conversations")
                return conversations
            else:
                # This might fail if we don't have the right permissions
                logging.warning(f"Could not access conversations: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Error getting incoming messages: {e}")
            return []
    
    def process_incoming_messages(self):
        """Process incoming DMs and auto-respond to keywords"""
        try:
            conversations = self.get_incoming_messages()
            processed_count = 0
            
            for conversation in conversations:
                # This is where we would process individual messages
                # Instagram Business API has limitations here
                # For now, we'll focus on the comment-reply strategy
                pass
            
            return processed_count
            
        except Exception as e:
            logging.error(f"Error processing incoming messages: {e}")
            return 0
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        try:
            if not self.check_login_status():
                logging.error("❌ Not logged in to Instagram Business API")
                return False
            
            logging.info("🚀 Starting Instagram Business API monitoring cycle")
            
            # Get recent posts
            posts = self.get_recent_posts()
            if not posts:
                logging.warning("⚠️ No posts found")
                return False
            
            total_processed = 0
            monitored_posts = 0
            
            for post in posts:
                if self.should_monitor_post(post):
                    monitored_posts += 1
                    logging.info(f"👁️ Monitoring post: {post['url']}")
                    
                    if self.process_post_comments(post):
                        total_processed += 1
                    
                    # Add delay between posts
                    time.sleep(random.uniform(3, 8))
                else:
                    logging.info(f"⏭️ Skipping post (doesn't match monitoring criteria)")
            
            # Process incoming DMs (limited capability)
            dm_processed = self.process_incoming_messages()
            
            logging.info(f"✅ Monitoring cycle complete - Monitored {monitored_posts} posts, processed {total_processed} posts with keyword matches, {dm_processed} DMs processed")
            
            return True
            
        except Exception as e:
            logging.error(f"Error in monitoring cycle: {e}")
            return False
    
    def get_stats(self):
        """Get bot statistics"""
        try:
            recent_comments = self.db.get_recent_processed_comments(100)
            
            stats = {
                'total_processed': len(recent_comments),
                'recent_activity': recent_comments[-10:] if recent_comments else [],
                'logged_in': self.logged_in,
                'api_type': 'Instagram Business API',
                'capabilities': [
                    'Monitor post comments',
                    'Reply to comments publicly',
                    'Encourage users to DM',
                    'Auto-respond to incoming DMs (limited)'
                ]
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return {'error': str(e)}

# For backward compatibility, create an alias
InstagramBot = InstagramBusinessBot 