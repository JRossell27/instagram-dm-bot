#!/usr/bin/env python3
"""
Instagram Business API Client
Uses official Instagram Graph API for professional DM automation
"""

import requests
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import Config

class InstagramBusinessAPI:
    """Instagram Business API client for DM automation using official Graph API"""
    
    def __init__(self):
        self.access_token = Config.INSTAGRAM_ACCESS_TOKEN
        self.user_id = Config.INSTAGRAM_USER_ID
        self.base_url = "https://graph.instagram.com/v21.0"
        self.logged_in = False
        self.last_login_check = None
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
    def login(self) -> bool:
        """
        Validate Instagram Business API credentials
        Returns True if authentication is successful
        """
        try:
            if not self.access_token or not self.user_id:
                self.logger.error("Instagram Business API credentials not configured")
                return False
            
            # Test API access with a simple call
            url = f"{self.base_url}/{self.user_id}"
            params = {
                'fields': 'id,username,account_type,media_count',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('username', 'Unknown')
                account_type = user_data.get('account_type', 'Unknown')
                
                self.logger.info(f"✅ Instagram Business API login successful - @{username} ({account_type})")
                self.logged_in = True
                self.last_login_check = datetime.now()
                return True
            else:
                self.logger.error(f"❌ Instagram Business API authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Instagram Business API login error: {e}")
            return False
    
    def get_conversations(self) -> List[Dict]:
        """
        Get Instagram DM conversations using Messenger API
        Returns list of conversation threads
        """
        try:
            if not self.logged_in:
                if not self.login():
                    return []
            
            # Note: Instagram Business messaging requires linking to a Facebook Page
            # This is a simplified version - full implementation would need Page ID
            url = f"{self.base_url}/{self.user_id}/conversations"
            params = {
                'platform': 'instagram',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                conversations = response.json().get('data', [])
                self.logger.info(f"Retrieved {len(conversations)} conversations")
                return conversations
            else:
                self.logger.warning(f"Failed to get conversations: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting conversations: {e}")
            return []
    
    def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send a DM using Instagram Business Messaging API
        
        Args:
            recipient_id: Instagram-scoped ID of the recipient
            message: Message text to send
            
        Returns:
            True if message was sent successfully
        """
        try:
            if not self.logged_in:
                if not self.login():
                    return False
            
            url = f"{self.base_url}/{self.user_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'recipient': {
                    'id': recipient_id
                },
                'message': {
                    'text': message
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                self.logger.info(f"✅ Message sent successfully to {recipient_id}")
                return True
            else:
                self.logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending message: {e}")
            return False
    
    def get_media_posts(self, limit: int = 25) -> List[Dict]:
        """
        Get Instagram posts using Business API
        
        Args:
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of post data dictionaries
        """
        try:
            if not self.logged_in:
                if not self.login():
                    return []
            
            url = f"{self.base_url}/{self.user_id}/media"
            params = {
                'fields': 'id,caption,media_type,media_url,permalink,timestamp,comments_count,like_count',
                'limit': limit,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                posts = response.json().get('data', [])
                self.logger.info(f"Retrieved {len(posts)} media posts")
                return posts
            else:
                self.logger.warning(f"Failed to get media posts: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting media posts: {e}")
            return []
    
    def get_post_comments(self, post_id: str) -> List[Dict]:
        """
        Get comments on a specific post
        
        Args:
            post_id: Instagram media ID
            
        Returns:
            List of comment data dictionaries
        """
        try:
            if not self.logged_in:
                if not self.login():
                    return []
            
            url = f"{self.base_url}/{post_id}/comments"
            params = {
                'fields': 'id,text,username,timestamp,from{id,username}',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                comments = response.json().get('data', [])
                self.logger.info(f"Retrieved {len(comments)} comments for post {post_id}")
                return comments
            else:
                self.logger.warning(f"Failed to get comments for post {post_id}: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting comments for post {post_id}: {e}")
            return []
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the long-lived access token (valid for 60 days)
        Should be called periodically to maintain authentication
        
        Returns:
            True if token was refreshed successfully
        """
        try:
            url = "https://graph.instagram.com/refresh_access_token"
            params = {
                'grant_type': 'ig_refresh_token',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                token_data = response.json()
                new_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 5184000)  # 60 days
                
                if new_token:
                    # Update configuration with new token
                    Config.INSTAGRAM_ACCESS_TOKEN = new_token
                    Config.save_runtime_config()
                    
                    self.access_token = new_token
                    self.logger.info(f"✅ Access token refreshed successfully (expires in {expires_in} seconds)")
                    return True
                else:
                    self.logger.error("❌ No new access token in refresh response")
                    return False
            else:
                self.logger.error(f"❌ Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error refreshing access token: {e}")
            return False
    
    def run_monitoring_cycle(self) -> bool:
        """
        Run a complete monitoring cycle using Business API
        This replaces the screen scraping approach with official API calls
        
        Returns:
            True if cycle completed successfully
        """
        try:
            self.logger.info("🔄 Starting Instagram Business API monitoring cycle")
            
            if not self.logged_in:
                if not self.login():
                    return False
            
            # Get recent posts
            posts = self.get_media_posts(Config.MAX_POSTS_TO_CHECK)
            
            if not posts:
                self.logger.warning("No posts retrieved from API")
                return False
            
            processed_count = 0
            
            for post in posts:
                try:
                    post_id = post['id']
                    caption = post.get('caption', '')
                    timestamp = post.get('timestamp', '')
                    
                    # Check if post matches monitoring criteria
                    if self.should_monitor_post(post):
                        # Get comments for this post
                        comments = self.get_post_comments(post_id)
                        
                        # Process comments that match keywords
                        for comment in comments:
                            if self.should_process_comment(comment):
                                success = self.process_comment(comment, post)
                                if success:
                                    processed_count += 1
                
                except Exception as e:
                    self.logger.error(f"Error processing post {post.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"✅ Monitoring cycle completed - processed {processed_count} comments")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in monitoring cycle: {e}")
            return False
    
    def should_monitor_post(self, post: Dict) -> bool:
        """Check if a post should be monitored based on configuration"""
        # Add your post filtering logic here
        # For now, monitor all posts
        return True
    
    def should_process_comment(self, comment: Dict) -> bool:
        """Check if a comment should be processed based on keywords"""
        comment_text = comment.get('text', '').lower()
        
        # Check for configured keywords
        for keyword in Config.KEYWORDS:
            if keyword.lower() in comment_text:
                return True
        
        return False
    
    def process_comment(self, comment: Dict, post: Dict) -> bool:
        """Process a comment that matches criteria and send DM"""
        try:
            comment_author = comment.get('from', {})
            author_id = comment_author.get('id')
            author_username = comment_author.get('username', 'unknown')
            
            if not author_id:
                self.logger.warning(f"No author ID found for comment from @{author_username}")
                return False
            
            # Prepare DM message
            message = Config.DM_MESSAGE.replace('{link}', Config.DEFAULT_LINK)
            
            # Send DM
            success = self.send_message(author_id, message)
            
            if success:
                self.logger.info(f"✅ DM sent to @{author_username} for comment: {comment.get('text', '')[:50]}...")
                
                # Save to database (if you have database integration)
                # self.save_processed_comment(comment, post)
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error processing comment: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Test the Instagram Business API client
    client = InstagramBusinessAPI()
    
    if client.login():
        print("✅ Instagram Business API login successful")
        
        # Test getting posts
        posts = client.get_media_posts(5)
        print(f"Retrieved {len(posts)} posts")
        
        # Test getting comments
        if posts:
            comments = client.get_post_comments(posts[0]['id'])
            print(f"Retrieved {len(comments)} comments for first post")
    else:
        print("❌ Instagram Business API login failed") 