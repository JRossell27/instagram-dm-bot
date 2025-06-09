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
            'keyword_strategy': getattr(Config, 'KEYWORD_STRATEGY', 'consent_required')
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
                        
                        # Only process new comments (not deleted)
                        if comment_data.get('verb') == 'add':
                            global bot
                            if bot and bot.logged_in:
                                # Process comment using ManyChat strategy
                                success = bot.process_comment_webhook(comment_data)
                                if success:
                                    bot_status['total_dms_sent'] += 1
                            else:
                                logging.warning("❌ Bot not initialized or not logged in")
            
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