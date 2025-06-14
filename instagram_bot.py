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

class InstagramBot:
    def __init__(self):
        self.db = Database()
        self.logged_in = False
        self.access_token = Config.INSTAGRAM_ACCESS_TOKEN
        self.user_id = Config.INSTAGRAM_USER_ID
        self.last_login_check = None
        self.login_check_interval = 300  # Check every 5 minutes
        
        # Direct DM messages for ManyChat strategy
        self.direct_dm_messages = [
            "Hi {username}! I saw your comment '{comment}' - here's the info you requested: {link} 🚀",
            "Hey {username}! Thanks for your interest! Here's what you're looking for: {link} ✨", 
            "Hi there! I noticed you commented '{comment}' - sending you the details now: {link} 📩",
            "Hello {username}! Here's the link you asked about: {link} Hope this helps! 🙌"
        ]
        
        # Encouragement messages for public replies (fallback)
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
    
    def check_comment_for_keywords(self, comment_text):
        """Check if comment contains any monitored keywords"""
        comment_lower = comment_text.lower()
        
        for keyword in Config.KEYWORDS:
            if keyword.lower() in comment_lower:
                return keyword
        
        return None
    
    def has_consent_to_dm(self, comment_text):
        """Check if comment contains explicit consent keywords for direct DM"""
        comment_lower = comment_text.lower()
        
        for consent_keyword in Config.CONSENT_KEYWORDS:
            if consent_keyword.lower() in comment_lower:
                logging.info(f"🎯 CONSENT DETECTED: '{consent_keyword}' - enabling direct DM")
                return True
        
        logging.info(f"⚠️ No explicit consent detected in comment: '{comment_text[:50]}...'")
        return False
    
    def reply_to_comment(self, comment_id, message):
        """Reply to a comment publicly"""
        try:
            # Instagram Business API comment reply endpoint
            url = f"https://graph.instagram.com/v21.0/{comment_id}/replies"
            
            data = {
                'message': message,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logging.info(f"✅ Comment reply sent successfully to comment {comment_id}")
                return True
            else:
                error_data = response.json() if response.text else {}
                logging.error(f"Failed to reply to comment {comment_id}: {response.status_code} - {error_data}")
                return False
                
        except Exception as e:
            logging.error(f"Error replying to comment {comment_id}: {e}")
            return False
    
    def get_dm_encouragement_message(self, keyword):
        """Generate an encouraging message for public reply"""
        template = random.choice(self.dm_encouragement_messages)
        return template.format(keyword=keyword.upper())
    
    def send_direct_message(self, user_id, message):
        """Send direct message to user (Instagram Messaging API)"""
        try:
            # Using Instagram Messaging API endpoint
            url = f"https://graph.instagram.com/v21.0/me/messages"
            
            data = {
                'recipient': {'id': user_id},
                'message': {'text': message},
                'access_token': self.access_token
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                logging.info(f"✅ Direct message sent successfully to user {user_id}")
                return True
            else:
                # Log detailed error for debugging
                error_data = response.json() if response.text else {}
                logging.error(f"Failed to send DM to {user_id}: {response.status_code} - {error_data}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending direct message to {user_id}: {e}")
            return False
    
    def process_comment_webhook(self, comment_data):
        """Process comment from webhook notification (ManyChat approach) - MAIN FUNCTION"""
        try:
            comment_id = comment_data.get('id')
            comment_text = comment_data.get('text', '')
            comment_author = comment_data.get('from', {})
            author_id = comment_author.get('id')
            author_username = comment_author.get('username', 'user')
            media_id = comment_data.get('media', {}).get('id', '')
            
            logging.info(f"🔔 WEBHOOK: New comment from @{author_username}: {comment_text[:50]}...")
            
            # POST FILTERING: Check if we should monitor this post
            if not Config.MONITOR_ALL_POSTS:
                if media_id not in Config.MONITORED_POST_IDS:
                    logging.info(f"⏭️ SKIPPING: Post {media_id} not in monitored posts list")
                    return False
            
            logging.info(f"✅ POST MONITORED: Processing comment on post {media_id}")
            
            # Check if already processed
            if self.db.is_comment_processed(comment_id):
                logging.info(f"Comment {comment_id} already processed, skipping")
                return False
            
            # Check for keywords
            matched_keyword = self.check_comment_for_keywords(comment_text)
            
            if matched_keyword:
                logging.info(f"🎯 KEYWORD MATCH: '{matched_keyword}' from @{author_username}")
                
                # Apply keyword strategy
                if Config.KEYWORD_STRATEGY == 'consent_required':
                    # MANYCHAT STRATEGY: Require explicit consent for direct DM
                    logging.info(f"🔍 Using consent_required strategy. Checking for consent in: '{comment_text}'")
                    logging.info(f"🔍 Available consent keywords: {Config.CONSENT_KEYWORDS}")
                    
                    if Config.ENABLE_DIRECT_DM and author_id:
                        has_consent = self.has_consent_to_dm(comment_text)
                        
                        if has_consent:
                            # DIRECT DM APPROACH (like ManyChat)
                            dm_message = self.get_direct_dm_message(author_username, comment_text, matched_keyword)
                            
                            if self.send_direct_message(author_id, dm_message):
                                # Log successful direct DM
                                self.db.add_processed_comment(
                                    comment_id=comment_id,
                                    post_id=media_id,
                                    username=author_username,
                                    user_id=author_id,
                                    comment_text=comment_text,
                                    keyword=matched_keyword,
                                    action_taken='direct_dm_sent_with_consent'
                                )
                                logging.info(f"✅ CONSENT DM sent to @{author_username}")
                                return True
                            else:
                                # DM failed - try comment reply as fallback
                                logging.info(f"🔄 DM failed, trying comment reply fallback for @{author_username}")
                                reply_message = Config.COMMENT_REPLY_CONSENT.format(username=author_username)
                                
                                if self.reply_to_comment(comment_id, reply_message):
                                    self.db.add_processed_comment(
                                        comment_id=comment_id,
                                        post_id=media_id,
                                        username=author_username,
                                        user_id=author_id,
                                        comment_text=comment_text,
                                        keyword=matched_keyword,
                                        action_taken='comment_reply_fallback'
                                    )
                                    logging.info(f"✅ Comment reply sent as fallback to @{author_username}")
                                    return True
                                else:
                                    logging.error(f"❌ Both DM and comment reply failed for @{author_username}")
                                    return False
                        else:
                            # No consent - encourage DM via public reply
                            logging.info(f"📢 NO CONSENT: Encouraging @{author_username} to DM with encouragement reply")
                            reply_message = Config.COMMENT_REPLY_ENCOURAGEMENT.format(username=author_username, keyword=matched_keyword)
                            
                            if self.reply_to_comment(comment_id, reply_message):
                                self.db.add_processed_comment(
                                    comment_id=comment_id,
                                    post_id=media_id,
                                    username=author_username,
                                    user_id=author_id,
                                    comment_text=comment_text,
                                    keyword=matched_keyword,
                                    action_taken='encouraged_to_dm'
                                )
                                logging.info(f"✅ Encouragement comment reply sent to @{author_username}")
                                return True
                            else:
                                logging.error(f"❌ Failed to send encouragement reply to @{author_username}")
                                return False
                
                elif Config.KEYWORD_STRATEGY == 'any_keyword':
                    # ANY KEYWORD STRATEGY: Send DM for any matched keyword (traditional approach)
                    logging.info(f"🔍 Using any_keyword strategy for '{matched_keyword}'")
                    
                    if Config.ENABLE_DIRECT_DM and author_id:
                        dm_message = self.get_direct_dm_message(author_username, comment_text, matched_keyword)
                        
                        if self.send_direct_message(author_id, dm_message):
                            # Log successful direct DM
                            self.db.add_processed_comment(
                                comment_id=comment_id,
                                post_id=media_id,
                                username=author_username,
                                user_id=author_id,
                                comment_text=comment_text,
                                keyword=matched_keyword,
                                action_taken='direct_dm_sent_any_keyword'
                            )
                            logging.info(f"✅ KEYWORD DM sent to @{author_username} for '{matched_keyword}'")
                            return True
                        else:
                            # DM failed - try comment reply as fallback
                            logging.info(f"🔄 DM failed, trying comment reply fallback for @{author_username}")
                            reply_message = Config.COMMENT_REPLY_INTEREST.format(username=author_username, keyword=matched_keyword)
                            
                            if self.reply_to_comment(comment_id, reply_message):
                                self.db.add_processed_comment(
                                    comment_id=comment_id,
                                    post_id=media_id,
                                    username=author_username,
                                    user_id=author_id,
                                    comment_text=comment_text,
                                    keyword=matched_keyword,
                                    action_taken='comment_reply_fallback_any_keyword'
                                )
                                logging.info(f"✅ Comment reply sent as fallback to @{author_username}")
                                return True
                            else:
                                logging.error(f"❌ Both DM and comment reply failed for @{author_username}")
                                return False
                
                return False
            else:
                logging.info(f"⏭️ No keywords matched in comment: '{comment_text[:50]}...'")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error processing webhook comment: {e}")
            return False
    
    def get_direct_dm_message(self, username, comment_text, keyword):
        """Generate direct DM message using ManyChat approach"""
        template = random.choice(self.direct_dm_messages)
        
        message = template.format(
            username=username,
            comment=comment_text[:30] + "..." if len(comment_text) > 30 else comment_text,
            keyword=keyword.upper(),
            link=Config.DEFAULT_LINK
        )
        
        return message
    
    def setup_webhooks(self):
        """Setup Instagram webhooks for real-time notifications"""
        try:
            # This would typically be done through Meta Developer Console
            # But we can verify webhook subscription programmatically
            
            webhook_url = f"{Config.WEBHOOK_BASE_URL}/webhook/instagram"
            
            # Subscribe to comment events
            subscription_url = f"https://graph.instagram.com/v21.0/{self.user_id}/subscribed_apps"
            
            data = {
                'subscribed_fields': 'comments',
                'access_token': self.access_token
            }
            
            response = requests.post(subscription_url, data=data)
            
            if response.status_code == 200:
                logging.info("✅ Webhook subscription configured successfully")
                return True
            else:
                logging.error(f"Webhook subscription failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error setting up webhooks: {e}")
            return False
    
    def get_stats(self):
        """Get bot statistics"""
        try:
            recent_comments = self.db.get_recent_processed_comments(100)
            
            stats = {
                'total_processed': len(recent_comments),
                'recent_activity': recent_comments[-10:] if recent_comments else [],
                'logged_in': self.logged_in,
                'api_type': 'Instagram Business API + Webhooks',
                'capabilities': [
                    'Real-time webhook processing',
                    'Direct DM sending with consent',
                    'Keyword detection and filtering',
                    'ManyChat-style automation'
                ]
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return {'error': str(e)}

# For backward compatibility, create an alias
InstagramBot = InstagramBot 