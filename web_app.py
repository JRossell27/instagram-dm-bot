#!/usr/bin/env python3
# Instagram DM Bot - Webhook-Optimized Architecture
# Deployment trigger: 2025-06-09 - Force redeploy with all navigation fixes
import os
import json
import logging
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from instagram_bot import InstagramBot
from config import Config
from database import Database
import time
import random
import requests
import secrets
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

# Global variables
bot = None
bot_status = {
    'webhook_active': False,
    'authenticated': False,
    'last_webhook_received': None,
    'total_webhooks_processed': 0,
    'total_dms_sent': 0,
    'error_message': None,
    'capabilities': {
        'real_time_webhooks': True,
        'direct_dm_sending': True,
        'consent_detection': True,
        'instant_response': True
    }
}

@app.context_processor
def inject_bot_status():
    """Make bot_status available to all templates"""
    return dict(bot_status=bot_status)

def init_bot():
    """Initialize the Instagram bot (authentication only)"""
    global bot
    try:
        bot = InstagramBot()
        if bot.login():
            bot_status['authenticated'] = True
            bot_status['error_message'] = None
            # Set up webhooks if not already done
            if hasattr(bot, 'setup_webhooks'):
                bot.setup_webhooks()
            return True
        else:
            bot_status['authenticated'] = False
            bot_status['error_message'] = "Failed to authenticate - check credentials"
            return False
    except Exception as e:
        bot_status['authenticated'] = False
        bot_status['error_message'] = f"Bot initialization error: {str(e)}"
        logging.error(f"Bot initialization error: {e}")
        return False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get recent activity
        db = Database()
        recent_comments = db.get_recent_processed_comments(10)
        
        # Update webhook statistics
        bot_status['total_dms_sent'] = len([c for c in recent_comments if 'dm_sent' in str(c)])
        
        # Get bot statistics
        stats = {
            'total_processed': len(db.get_recent_processed_comments(1000)),
            'recent_activity': recent_comments,
            'keywords': Config.KEYWORDS,
            'consent_keywords': Config.CONSENT_KEYWORDS,
            'interest_keywords': Config.INTEREST_KEYWORDS,
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK,
            'webhook_enabled': True,
            'real_time_processing': True,
            
            # New configuration data
            'monitor_all_posts': Config.MONITOR_ALL_POSTS,
            'monitored_post_ids': Config.MONITORED_POST_IDS,
            'keyword_strategy': getattr(Config, 'KEYWORD_STRATEGY', 'consent_required'),
            
            # Comment reply templates
            'comment_reply_consent': getattr(Config, 'COMMENT_REPLY_CONSENT', 'Hi @{username}! I saw your request. Please DM me and I\'ll send you the link! 📩'),
            'comment_reply_interest': getattr(Config, 'COMMENT_REPLY_INTEREST', 'Hi @{username}! I saw your interest in \'{keyword}\'. Please DM me and I\'ll send you the details! 📩'),
            'comment_reply_encouragement': getattr(Config, 'COMMENT_REPLY_ENCOURAGEMENT', 'Great question @{username}! DM me \'{keyword}\' for the full details 📩')
        }
        
        # Get Instagram account info
        account_info = get_instagram_account_info()
        
        return render_template('dashboard.html', 
                             bot_status=bot_status, 
                             stats=stats,
                             account_info=account_info)
                             
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('dashboard.html', 
                             bot_status=bot_status, 
                             stats={},
                             account_info=None)

@app.route('/activate', methods=['POST'])
def activate_bot():
    """Activate webhook processing (replaces start_bot)"""
    try:
        if not bot_status['authenticated']:
            if init_bot():
                bot_status['webhook_active'] = True
                flash('✅ Webhook processing activated! Bot ready for real-time comments.', 'success')
            else:
                flash(f'❌ Failed to activate: {bot_status["error_message"]}', 'error')
        else:
            bot_status['webhook_active'] = True
            flash('✅ Webhook processing is now active!', 'success')
    except Exception as e:
        flash(f'❌ Error activating webhook processing: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/deactivate', methods=['POST'])
def deactivate_bot():
    """Deactivate webhook processing (replaces stop_bot)"""
    try:
        bot_status['webhook_active'] = False
        flash('⏸️ Webhook processing deactivated.', 'success')
    except Exception as e:
        flash(f'❌ Error deactivating: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/test-webhook', methods=['POST'])
def test_webhook_processing():
    """Test webhook processing with sample data"""
    try:
        if not bot or not bot.logged_in:
            if not init_bot():
                flash(f'❌ Failed to initialize bot: {bot_status["error_message"]}', 'error')
                return redirect(url_for('dashboard'))
        
        # Create test comment data
        test_comment = {
            'id': f'test_comment_{int(time.time())}',
            'text': request.form.get('test_comment', 'dm me please!'),
            'from': {
                'id': 'test_user_123',
                'username': request.form.get('test_username', 'testuser')
            },
            'media': {
                'id': 'test_post_456'
            },
            'verb': 'add'
        }
        
        # Process the test comment
        success = bot.process_comment_webhook(test_comment)
        
        if success:
            flash('✅ Webhook test successful! Check logs for details.', 'success')
        else:
            flash('⚠️ Webhook test completed - check logs for results.', 'info')
        
    except Exception as e:
        flash(f'❌ Error testing webhook: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/config')
def config_page():
    """Configuration page (simplified for webhook architecture)"""
    try:
        config_data = {
            'keywords': Config.KEYWORDS,
            'consent_keywords': Config.CONSENT_KEYWORDS,
            'interest_keywords': Config.INTEREST_KEYWORDS,
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK,
            'enable_direct_dm': Config.ENABLE_DIRECT_DM,
            'webhook_base_url': Config.WEBHOOK_BASE_URL,
            'webhook_verify_token': Config.WEBHOOK_VERIFY_TOKEN
        }
        
        return render_template('config.html', config=config_data, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Config page error: {e}")
        flash(f'Error loading configuration: {str(e)}', 'error')
        return render_template('config.html', config={}, bot_status=bot_status)

@app.route('/logs')
def logs_page():
    """Logs page"""
    try:
        # Read recent log entries
        log_entries = []
        if os.path.exists('instagram_bot.log'):
            with open('instagram_bot.log', 'r') as f:
                lines = f.readlines()
                # Get last 100 lines
                log_entries = lines[-100:] if len(lines) > 100 else lines
                log_entries.reverse()  # Show newest first
        
        return render_template('logs.html', logs=log_entries, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Logs page error: {e}")
        flash(f'Error loading logs: {str(e)}', 'error')
        return render_template('logs.html', logs=[], bot_status=bot_status)

@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    return jsonify(bot_status)

@app.route('/api/stats')
def api_stats():
    """Return bot statistics as JSON"""
    db = Database()
    recent_comments = db.get_recent_processed_comments(10)
    
    return jsonify({
        'total_processed': len(db.get_recent_processed_comments(1000)),
        'total_dms_sent': len([c for c in recent_comments if 'dm_sent' in str(c)]),
        'webhook_active': bot_status['webhook_active'],
        'authenticated': bot_status['authenticated'],
        'recent_activity': recent_comments[:5],  # Last 5 for API
        'last_update': datetime.now().isoformat()
    })

@app.route('/api/update-post-monitoring', methods=['POST'])
def api_update_post_monitoring():
    """Update post monitoring configuration"""
    try:
        data = request.get_json()
        monitor_all = data.get('monitor_all_posts', False)
        monitored_ids = data.get('monitored_post_ids', [])
        
        # Update configuration
        Config.MONITOR_ALL_POSTS = monitor_all
        Config.MONITORED_POST_IDS = monitored_ids
        
        # Save to runtime config
        if Config.save_runtime_config():
            logging.info(f"Updated post monitoring: all_posts={monitor_all}, specific_ids={len(monitored_ids)}")
            return jsonify({
                'success': True,
                'message': f"Post monitoring updated: {'All posts' if monitor_all else f'{len(monitored_ids)} specific posts'}"
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save configuration'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating post monitoring: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating post monitoring: {str(e)}'
        }), 500

@app.route('/api/update-keyword-strategy', methods=['POST'])
def api_update_keyword_strategy():
    """Update keyword strategy configuration"""
    try:
        data = request.get_json()
        strategy = data.get('keyword_strategy', 'consent_required')
        
        if strategy not in ['consent_required', 'any_keyword']:
            return jsonify({
                'success': False,
                'message': 'Invalid keyword strategy. Must be "consent_required" or "any_keyword"'
            }), 400
        
        # Update configuration
        Config.KEYWORD_STRATEGY = strategy
        
        # Save to runtime config
        if Config.save_runtime_config():
            strategy_name = "Consent Required (ManyChat Style)" if strategy == 'consent_required' else "Any Keyword (Traditional)"
            logging.info(f"Updated keyword strategy to: {strategy}")
            return jsonify({
                'success': True,
                'message': f"Keyword strategy updated to: {strategy_name}"
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save configuration'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating keyword strategy: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating keyword strategy: {str(e)}'
        }), 500

@app.route('/api/save_comment_templates', methods=['POST'])
def api_save_comment_templates():
    """Save comment reply templates"""
    try:
        data = request.get_json()
        
        # Update Config with new templates
        Config.COMMENT_REPLY_CONSENT = data.get('consent_reply', Config.COMMENT_REPLY_CONSENT)
        Config.COMMENT_REPLY_INTEREST = data.get('interest_reply', Config.COMMENT_REPLY_INTEREST)
        Config.COMMENT_REPLY_ENCOURAGEMENT = data.get('encouragement_reply', Config.COMMENT_REPLY_ENCOURAGEMENT)
        
        # Save to runtime config
        if Config.save_runtime_config():
            logging.info("Comment reply templates updated successfully")
            return jsonify({
                'success': True,
                'message': 'Comment reply templates saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save comment templates'
            }), 500
            
    except Exception as e:
        logging.error(f"Error saving comment templates: {e}")
        return jsonify({
            'success': False,
            'message': f'Error saving comment templates: {str(e)}'
        }), 500

@app.route('/manage_keywords')
def manage_keywords():
    """Manage keywords and filtering settings (simplified for webhook architecture)"""
    try:
        current_settings = {
            'keywords': Config.KEYWORDS,
            'consent_keywords': getattr(Config, 'CONSENT_KEYWORDS', []),
            'interest_keywords': getattr(Config, 'INTEREST_KEYWORDS', []),
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK,
            'enable_direct_dm': getattr(Config, 'ENABLE_DIRECT_DM', True)
        }
        
        return render_template('manage_keywords.html', 
                             settings=current_settings,
                             bot_status=bot_status)
                             
    except Exception as e:
        logging.error(f"Error in manage_keywords: {e}")
        return render_template('manage_keywords.html', 
                             error=f"Error loading settings: {e}",
                             bot_status=bot_status)

@app.route('/update_keywords', methods=['POST'])
def update_keywords():
    """Update keywords and filtering settings"""
    try:
        # Update keywords
        keywords_text = request.form.get('keywords', '').strip()
        Config.KEYWORDS = [k.strip() for k in keywords_text.split('\n') if k.strip()]
        
        # Update consent keywords (for direct DM)
        consent_text = request.form.get('consent_keywords', '').strip()
        Config.CONSENT_KEYWORDS = [k.strip() for k in consent_text.split('\n') if k.strip()]
        
        # Update interest keywords (for public reply)
        interest_text = request.form.get('interest_keywords', '').strip()
        Config.INTEREST_KEYWORDS = [k.strip() for k in interest_text.split('\n') if k.strip()]
        
        # Update DM settings
        Config.DM_MESSAGE = request.form.get('dm_message', Config.DM_MESSAGE)
        Config.DEFAULT_LINK = request.form.get('default_link', Config.DEFAULT_LINK)
        Config.ENABLE_DIRECT_DM = 'enable_direct_dm' in request.form
        
        # Save configuration changes to persist across restarts
        Config.save_runtime_config()
        
        flash("✅ Keyword settings updated successfully!", 'success')
        
        return redirect('/manage_keywords')
        
    except Exception as e:
        logging.error(f"Error updating keywords: {e}")
        flash(f"❌ Error updating settings: {e}", 'error')
        return redirect('/manage_keywords')

@app.route('/webhook/instagram', methods=['GET', 'POST'])
def instagram_webhook():
    """Handle Instagram webhook notifications (ManyChat approach)"""
    if request.method == 'GET':
        # Webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == Config.WEBHOOK_VERIFY_TOKEN:
            logging.info("✅ Instagram webhook verified successfully")
            return challenge
        else:
            logging.error("❌ Instagram webhook verification failed")
            return 'Forbidden', 403
    
    elif request.method == 'POST':
        # Process webhook notification
        try:
            data = request.get_json()
            logging.info(f"🔔 Instagram webhook received: {data}")
            
            # Update webhook stats
            bot_status['last_webhook_received'] = datetime.now()
            bot_status['total_webhooks_processed'] += 1
            
            # Only process if webhook is active
            if not bot_status['webhook_active']:
                logging.warning("⚠️ Webhook received but processing is deactivated")
                return 'OK', 200
            
            # Process each entry in the webhook data
            for entry in data.get('entry', []):
                # Process comment changes
                for changes in entry.get('changes', []):
                    if changes.get('field') == 'comments':
                        comment_data = changes.get('value', {})
                        
                        # Process comments (Instagram webhooks for comments are typically 'add' events)
                        # Only skip if explicitly marked as 'remove' or 'hide'
                        comment_verb = comment_data.get('verb', 'add')  # Default to 'add' if not specified
                        
                        if comment_verb not in ['remove', 'hide']:
                            logging.info(f"🔄 Processing comment webhook (verb: {comment_verb})")
                            global bot
                            if bot and bot.logged_in:
                                # Process comment using ManyChat strategy
                                success = bot.process_comment_webhook(comment_data)
                                if success:
                                    bot_status['total_dms_sent'] += 1
                                    logging.info(f"✅ Comment processed successfully - DM sent!")
                                else:
                                    logging.warning(f"⚠️ Comment processed but no DM sent")
                            else:
                                logging.warning("❌ Bot not initialized or not logged in")
                        else:
                            logging.info(f"⏭️ Skipping {comment_verb} comment event")
            
            return 'OK', 200
            
        except Exception as e:
            logging.error(f"❌ Error processing Instagram webhook: {e}")
            return 'Error', 500

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Test webhook functionality with sample data"""
    try:
        # Sample comment data for testing
        test_comment_data = {
            'id': 'test_comment_123',
            'text': request.json.get('comment_text', 'I want the link please!'),
            'from': {
                'id': request.json.get('user_id', '123456789'),
                'username': request.json.get('username', 'testuser')
            },
            'media': {
                'id': 'test_post_456'
            },
            'verb': 'add'
        }
        
        global bot
        if bot and bot.logged_in and bot_status['webhook_active']:
            result = bot.process_comment_webhook(test_comment_data)
            return jsonify({
                'success': result,
                'message': 'Test webhook processed successfully',
                'comment_data': test_comment_data,
                'webhook_active': bot_status['webhook_active']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Webhook processing not active or bot not authenticated',
                'webhook_active': bot_status['webhook_active'],
                'authenticated': bot_status['authenticated']
            }), 400
            
    except Exception as e:
        logging.error(f"Error in test webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/webhook-test')
def webhook_test_page():
    """Webhook testing interface page"""
    return render_template('webhook_test.html', bot_status=bot_status)

@app.route('/instagram-setup')
def instagram_setup():
    """Instagram setup and login page - DEPRECATED"""
    flash('⚠️ Please use the Instagram Business login instead.', 'info')
    return redirect(url_for('instagram_login'))

@app.route('/instagram_login')
def instagram_login():
    """Instagram Business OAuth login page"""
    try:
        # Pass Instagram App ID to template for OAuth
        instagram_app_id = Config.INSTAGRAM_APP_ID or ''
        return render_template('instagram_login.html', 
                             instagram_app_id=instagram_app_id,
                             bot_status=bot_status)
                             
    except Exception as e:
        logging.error(f"Error in Instagram login page: {e}")
        flash(f'Error loading Instagram login: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/debug/oauth-config')
def debug_oauth_config():
    """Debug route to show OAuth configuration"""
    config_info = {
        'webhook_base_url': Config.WEBHOOK_BASE_URL,
        'redirect_uri': f"{Config.WEBHOOK_BASE_URL}/auth/instagram/callback",
        'app_id': Config.INSTAGRAM_APP_ID or 'NOT SET',
        'app_secret_set': bool(Config.INSTAGRAM_APP_SECRET),
        'current_host': request.host_url.rstrip('/')
    }
    
    return jsonify(config_info)

@app.route('/auth/instagram')
def auth_instagram():
    """Start Instagram OAuth flow"""
    try:
        if not Config.INSTAGRAM_APP_ID:
            flash('❌ Instagram Business App not configured. Please set INSTAGRAM_APP_ID environment variable.', 'error')
            return redirect(url_for('instagram_login'))
        
        if not Config.INSTAGRAM_APP_SECRET:
            flash('❌ Instagram Business App Secret not configured. Please set INSTAGRAM_APP_SECRET environment variable.', 'error')
            return redirect(url_for('instagram_login'))
        
        # Use current host if WEBHOOK_BASE_URL is not properly set
        if not Config.WEBHOOK_BASE_URL or Config.WEBHOOK_BASE_URL == 'https://your-app.onrender.com':
            base_url = request.host_url.rstrip('/')
            redirect_uri = f"{base_url}/auth/instagram/callback"
        else:
            redirect_uri = f"{Config.WEBHOOK_BASE_URL}/auth/instagram/callback"
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Instagram OAuth URL
        auth_url = 'https://www.instagram.com/oauth/authorize'
        params = {
            'client_id': Config.INSTAGRAM_APP_ID,
            'redirect_uri': redirect_uri,
            'scope': 'instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments',
            'response_type': 'code',
            'state': state
        }
        
        # Log the redirect URI for debugging
        logging.info(f"🔗 Instagram OAuth redirect URI: {redirect_uri}")
        
        auth_url_with_params = f"{auth_url}?{urllib.parse.urlencode(params)}"
        return redirect(auth_url_with_params)
        
    except Exception as e:
        logging.error(f"Error starting Instagram OAuth: {e}")
        flash(f'❌ Error starting Instagram authentication: {str(e)}', 'error')
        return redirect(url_for('instagram_login'))

@app.route('/auth/instagram/callback')
def auth_instagram_callback():
    """Handle Instagram OAuth callback"""
    try:
        # Verify state parameter
        if request.args.get('state') != session.get('oauth_state'):
            flash('❌ Invalid state parameter. Authentication failed.', 'error')
            return redirect(url_for('instagram_login'))
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error_description', 'Unknown error')
            flash(f'❌ Instagram authentication failed: {error}', 'error')
            return redirect(url_for('instagram_login'))
        
        # Use same redirect URI logic as auth flow
        if not Config.WEBHOOK_BASE_URL or Config.WEBHOOK_BASE_URL == 'https://your-app.onrender.com':
            base_url = request.host_url.rstrip('/')
            redirect_uri = f"{base_url}/auth/instagram/callback"
        else:
            redirect_uri = f"{Config.WEBHOOK_BASE_URL}/auth/instagram/callback"
        
        # Exchange code for access token
        token_url = 'https://www.instagram.com/oauth/access_token'
        token_data = {
            'client_id': Config.INSTAGRAM_APP_ID,
            'client_secret': Config.INSTAGRAM_APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code
        }
        
        logging.info(f"🔄 Token exchange using redirect URI: {redirect_uri}")
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            token_info = response.json()
            Config.INSTAGRAM_ACCESS_TOKEN = token_info.get('access_token')
            Config.INSTAGRAM_USER_ID = token_info.get('user_id')
            
            # Update webhook base URL to current host if not set properly
            if not Config.WEBHOOK_BASE_URL or Config.WEBHOOK_BASE_URL == 'https://your-app.onrender.com':
                Config.WEBHOOK_BASE_URL = request.host_url.rstrip('/')
                logging.info(f"📍 Updated WEBHOOK_BASE_URL to: {Config.WEBHOOK_BASE_URL}")
            
            # Save configuration
            Config.save_runtime_config()
            
            # Initialize bot with new credentials
            global bot
            bot = None
            if init_bot():
                flash('✅ Instagram Business account connected successfully!', 'success')
            else:
                flash('⚠️ Instagram connected but bot initialization failed.', 'warning')
            
            return redirect(url_for('dashboard'))
        else:
            error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            logging.error(f"❌ Token exchange failed: {response.status_code} - {error_info}")
            flash(f'❌ Failed to exchange authorization code for access token. Status: {response.status_code}', 'error')
            return redirect(url_for('instagram_login'))
            
    except Exception as e:
        logging.error(f"Error in Instagram OAuth callback: {e}")
        flash(f'❌ Error processing Instagram authentication: {str(e)}', 'error')
        return redirect(url_for('instagram_login'))

@app.route('/instagram_login_manual')
def instagram_login_manual():
    """Manual Instagram session setup page - DEPRECATED"""
    flash('⚠️ Manual session login is deprecated. Please use Instagram Business OAuth instead.', 'warning')
    return redirect(url_for('instagram_login'))

@app.route('/update_instagram_login', methods=['POST'])
def update_instagram_login():
    """Update Instagram login credentials - DEPRECATED"""
    flash('⚠️ Manual session login is no longer supported. Please use Instagram Business OAuth.', 'warning')
    return redirect(url_for('instagram_login'))

def get_instagram_account_info():
    """Get current Instagram account information for dashboard display"""
    try:
        if not Config.INSTAGRAM_ACCESS_TOKEN or not Config.INSTAGRAM_USER_ID:
            return None
            
        # Get account info from Instagram Business API
        url = f"https://graph.instagram.com/v21.0/{Config.INSTAGRAM_USER_ID}"
        params = {
            'fields': 'id,username,account_type,profile_picture_url,followers_count,media_count',
            'access_token': Config.INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            account_data = response.json()
            return {
                'username': account_data.get('username', 'Unknown'),
                'account_type': account_data.get('account_type', 'Unknown'),
                'profile_picture': account_data.get('profile_picture_url', ''),
                'followers_count': account_data.get('followers_count', 0),
                'media_count': account_data.get('media_count', 0),
                'user_id': account_data.get('id', ''),
                'authenticated': True
            }
        else:
            logging.warning(f"Failed to get account info: {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting Instagram account info: {e}")
        return None

@app.route('/manage-posts')
def manage_posts():
    """Manage which posts to monitor - fetches real posts from Instagram"""
    try:
        if not Config.INSTAGRAM_ACCESS_TOKEN or not Config.INSTAGRAM_USER_ID:
            flash('❌ Instagram Business account not connected. Please authenticate first.', 'error')
            return redirect(url_for('instagram_login'))
        
        # Fetch recent posts from Instagram Business API
        posts_url = f"https://graph.instagram.com/v21.0/{Config.INSTAGRAM_USER_ID}/media"
        params = {
            'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp',
            'limit': 25,  # Get last 25 posts
            'access_token': Config.INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.get(posts_url, params=params)
        
        if response.status_code == 200:
            posts_data = response.json()
            posts = []
            
            for post in posts_data.get('data', []):
                # Only include posts that support comments (images/carousels)
                if post.get('media_type') in ['IMAGE', 'CAROUSEL_ALBUM']:
                    posts.append({
                        'id': post.get('id'),
                        'caption': (post.get('caption') or 'No caption')[:100] + ('...' if len(post.get('caption', '')) > 100 else ''),
                        'media_type': post.get('media_type'),
                        'media_url': post.get('media_url') or post.get('thumbnail_url'),
                        'permalink': post.get('permalink'),
                        'timestamp': post.get('timestamp'),
                        'is_monitored': post.get('id') in Config.MONITORED_POST_IDS
                    })
            
            return render_template('manage_posts.html', 
                                 posts=posts,
                                 monitor_all=Config.MONITOR_ALL_POSTS,
                                 bot_status=bot_status)
        else:
            error_data = response.json() if response.text else {}
            flash(f'❌ Failed to fetch posts: {error_data.get("error", {}).get("message", "Unknown error")}', 'error')
            return render_template('manage_posts.html', posts=[], monitor_all=Config.MONITOR_ALL_POSTS, bot_status=bot_status)
            
    except Exception as e:
        logging.error(f"Error in manage posts: {e}")
        flash(f'❌ Error loading posts: {str(e)}', 'error')
        return render_template('manage_posts.html', posts=[], monitor_all=Config.MONITOR_ALL_POSTS, bot_status=bot_status)

@app.route('/update-monitored-posts', methods=['POST'])
def update_monitored_posts():
    """Update which posts are being monitored"""
    try:
        monitor_all = 'monitor_all' in request.form
        selected_posts = request.form.getlist('monitored_posts')
        
        Config.MONITOR_ALL_POSTS = monitor_all
        Config.MONITORED_POST_IDS = selected_posts if not monitor_all else []
        
        # Save configuration
        Config.save_runtime_config()
        
        if monitor_all:
            flash('✅ Now monitoring ALL posts for comments!', 'success')
        elif selected_posts:
            flash(f'✅ Now monitoring {len(selected_posts)} selected posts!', 'success')
        else:
            flash('⚠️ No posts selected for monitoring. Bot will not process any comments.', 'warning')
        
        return redirect(url_for('manage_posts'))
        
    except Exception as e:
        logging.error(f"Error updating monitored posts: {e}")
        flash(f'❌ Error updating posts: {str(e)}', 'error')
        return redirect(url_for('manage_posts'))

if __name__ == '__main__':
    # Load runtime configuration on startup
    print("🔧 Loading runtime configuration...")
    Config.load_runtime_config()
    
    # Initialize on startup
    print("🤖 Initializing Instagram bot for webhook processing...")
    init_bot()
    
    # Check if running in production
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting webhook-powered Instagram automation")
    print(f"📍 Debug mode: {debug}")
    print(f"🔗 Default link: {Config.DEFAULT_LINK}")
    print(f"⚡ Real-time webhook processing: ENABLED")
    print(f"🎯 Keywords: {Config.KEYWORDS}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 