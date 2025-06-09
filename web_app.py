#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
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
scheduler = None
bot_status = {
    'running': False,
    'last_run': None,
    'next_run': None,
    'total_dms_sent': 0,
    'posts_monitored': 0,
    'error_message': None
}

@app.context_processor
def inject_bot_status():
    """Make bot_status available to all templates"""
    return dict(bot_status=bot_status)

def init_bot():
    """Initialize the Instagram bot"""
    global bot
    try:
        bot = InstagramBot()
        if bot.login():
            bot_status['error_message'] = None
            return True
        else:
            bot_status['error_message'] = "Failed to login - check credentials"
            return False
    except Exception as e:
        bot_status['error_message'] = f"Bot initialization error: {str(e)}"
        logging.error(f"Bot initialization error: {e}")
        return False

def run_bot_cycle():
    """Run a single bot monitoring cycle"""
    global bot_status
    
    try:
        if not bot or not bot.logged_in:
            if not init_bot():
                return
        
        logging.info("Starting scheduled bot cycle")
        bot_status['last_run'] = datetime.now()
        
        # Run the monitoring cycle
        success = bot.run_monitoring_cycle()
        
        if success:
            # Update statistics
            db = Database()
            recent_comments = db.get_recent_processed_comments(100)
            bot_status['total_dms_sent'] = len(recent_comments)
            
            logging.info("Bot cycle completed successfully")
        else:
            bot_status['error_message'] = "Bot cycle failed - check logs"
            
    except Exception as e:
        bot_status['error_message'] = f"Error in bot cycle: {str(e)}"
        logging.error(f"Error in bot cycle: {e}")

def start_scheduler():
    """Start the background scheduler"""
    global scheduler, bot_status
    
    if scheduler and scheduler.running:
        return
    
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=run_bot_cycle,
            trigger="interval",
            seconds=Config.CHECK_INTERVAL,
            id='bot_cycle'
        )
        scheduler.start()
        bot_status['running'] = True
        bot_status['next_run'] = datetime.now() + timedelta(seconds=Config.CHECK_INTERVAL)
        logging.info(f"Scheduler started - running every {Config.CHECK_INTERVAL} seconds")
        
    except Exception as e:
        bot_status['error_message'] = f"Scheduler error: {str(e)}"
        logging.error(f"Scheduler error: {e}")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler, bot_status
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        scheduler = None
        bot_status['running'] = False
        bot_status['next_run'] = None
        logging.info("Scheduler stopped")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get recent activity
        db = Database()
        recent_comments = db.get_recent_processed_comments(10)
        
        # Get bot statistics
        stats = {
            'total_processed': len(db.get_recent_processed_comments(1000)),
            'recent_activity': recent_comments,
            'keywords': Config.KEYWORDS,
            'check_interval': Config.CHECK_INTERVAL,
            'monitor_all_posts': Config.MONITOR_ALL_POSTS,
            'specific_posts': len(Config.SPECIFIC_POST_IDS) if Config.SPECIFIC_POST_IDS else 0,
            'required_hashtags': Config.REQUIRED_HASHTAGS,
            'required_phrases': Config.REQUIRED_CAPTION_WORDS,
            'max_age_days': Config.MAX_POST_AGE_DAYS,
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK,
        }
        
        return render_template('dashboard.html', 
                             bot_status=bot_status, 
                             stats=stats)
                             
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('dashboard.html', 
                             bot_status=bot_status, 
                             stats={})

@app.route('/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    try:
        if not bot_status['running']:
            if init_bot():
                start_scheduler()
                flash('Bot started successfully!', 'success')
            else:
                flash(f'Failed to start bot: {bot_status["error_message"]}', 'error')
        else:
            flash('Bot is already running!', 'info')
    except Exception as e:
        flash(f'Error starting bot: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    try:
        stop_scheduler()
        flash('Bot stopped successfully!', 'success')
    except Exception as e:
        flash(f'Error stopping bot: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/run-once', methods=['POST'])
def run_once():
    """Run bot once for testing"""
    try:
        if not bot or not bot.logged_in:
            if not init_bot():
                flash(f'Failed to initialize bot: {bot_status["error_message"]}', 'error')
                return redirect(url_for('dashboard'))
        
        # Run in background thread to avoid blocking
        def run_test():
            run_bot_cycle()
        
        thread = Thread(target=run_test)
        thread.start()
        
        flash('Test run started - check logs for results', 'info')
        
    except Exception as e:
        flash(f'Error running test: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/config')
def config_page():
    """Configuration page"""
    try:
        config_data = {
            'keywords': Config.KEYWORDS,
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK,
            'check_interval': Config.CHECK_INTERVAL,
            'monitor_all_posts': Config.MONITOR_ALL_POSTS,
            'specific_post_ids': Config.SPECIFIC_POST_IDS,
            'required_hashtags': Config.REQUIRED_HASHTAGS,
            'required_caption_words': Config.REQUIRED_CAPTION_WORDS,
            'max_post_age_days': Config.MAX_POST_AGE_DAYS,
            'only_posts_with_links': Config.ONLY_POSTS_WITH_LINKS,
        }
        
        return render_template('config.html', config=config_data, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Config page error: {e}")
        flash(f'Error loading configuration: {str(e)}', 'error')
        return render_template('config.html', config={}, bot_status=bot_status)

@app.route('/posts')
def posts_page():
    """Posts selection page"""
    try:
        if not bot or not bot.logged_in:
            if not init_bot():
                flash(f'Failed to connect to Instagram: {bot_status["error_message"]}', 'error')
                return render_template('posts.html', posts=[], bot_status=bot_status)
        
        posts = bot.get_recent_posts(50)  # Get more posts for selection
        posts_data = []
        
        for post in posts:
            post_info = {
                'id': post.code,
                'url': f"https://www.instagram.com/p/{post.code}/",
                'caption': (post.caption_text[:100] + "...") if post.caption_text else "No caption",
                'date': post.taken_at.strftime("%Y-%m-%d %H:%M"),
                'is_monitored': bot.should_monitor_post(post)
            }
            posts_data.append(post_info)
        
        return render_template('posts.html', posts=posts_data, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Posts page error: {e}")
        flash(f'Error loading posts: {str(e)}', 'error')
        return render_template('posts.html', posts=[], bot_status=bot_status)

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
    """API endpoint for statistics"""
    try:
        db = Database()
        recent_comments = db.get_recent_processed_comments(10)
        
        return jsonify({
            'recent_activity': recent_comments,
            'total_processed': len(db.get_recent_processed_comments(1000)),
            'bot_running': bot_status['running'],
            'last_run': bot_status['last_run'].isoformat() if bot_status['last_run'] else None,
            'next_run': bot_status['next_run'].isoformat() if bot_status['next_run'] else None,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/manage_posts')
def manage_posts():
    """Manage specific posts to monitor"""
    try:
        if not bot or not bot.logged_in:
            return render_template('manage_posts.html', 
                                 error="Please login first to see your posts",
                                 bot_status=bot_status)
        
        # Get recent posts for selection
        recent_posts = bot.get_recent_posts(50)  # Get more posts for management
        
        # Get current monitored posts from config
        current_posts = Config.SPECIFIC_POST_IDS if hasattr(Config, 'SPECIFIC_POST_IDS') else []
        
        # Format posts for display
        formatted_posts = []
        for post in recent_posts:
            formatted_posts.append({
                'code': post.code,
                'url': f"https://www.instagram.com/p/{post.code}/",
                'caption': (post.caption_text[:100] + "...") if post.caption_text else "No caption",
                'date': post.taken_at.strftime("%Y-%m-%d %H:%M"),
                'monitored': post.code in current_posts
            })
        
        return render_template('manage_posts.html', 
                             posts=formatted_posts,
                             current_posts=current_posts,
                             bot_status=bot_status)
                             
    except Exception as e:
        logging.error(f"Error in manage_posts: {e}")
        return render_template('manage_posts.html', 
                             error=f"Error loading posts: {e}",
                             bot_status=bot_status)

@app.route('/update_monitored_posts', methods=['POST'])
def update_monitored_posts():
    """Update which posts should be monitored"""
    try:
        selected_posts = request.form.getlist('selected_posts')
        
        # Update config with selected posts
        Config.SPECIFIC_POST_IDS = selected_posts
        Config.MONITOR_ALL_POSTS = len(selected_posts) == 0  # If no specific posts, monitor all
        
        # Save configuration changes to persist across restarts
        Config.save_runtime_config()
        
        flash(f"Updated monitoring for {len(selected_posts)} posts", 'success')
        
        return redirect('/manage_posts')
        
    except Exception as e:
        logging.error(f"Error updating monitored posts: {e}")
        flash(f"Error updating posts: {e}", 'error')
        return redirect('/manage_posts')

@app.route('/manage_keywords')
def manage_keywords():
    """Manage keywords and filtering settings"""
    try:
        current_settings = {
            'keywords': Config.KEYWORDS,
            'required_hashtags': getattr(Config, 'REQUIRED_HASHTAGS', []),
            'required_words': getattr(Config, 'REQUIRED_CAPTION_WORDS', []),
            'max_post_age': getattr(Config, 'MAX_POST_AGE_DAYS', 7),
            'only_with_links': getattr(Config, 'ONLY_POSTS_WITH_LINKS', False),
            'monitor_all_posts': getattr(Config, 'MONITOR_ALL_POSTS', True),
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK
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
        
        # Update hashtags
        hashtags_text = request.form.get('required_hashtags', '').strip()
        Config.REQUIRED_HASHTAGS = [h.strip() for h in hashtags_text.split('\n') if h.strip()]
        
        # Update caption words
        words_text = request.form.get('required_words', '').strip()
        Config.REQUIRED_CAPTION_WORDS = [w.strip() for w in words_text.split('\n') if w.strip()]
        
        # Update other settings
        Config.MAX_POST_AGE_DAYS = int(request.form.get('max_post_age', 7))
        Config.ONLY_POSTS_WITH_LINKS = 'only_with_links' in request.form
        Config.MONITOR_ALL_POSTS = 'monitor_all_posts' in request.form
        
        # Update DM settings
        Config.DM_MESSAGE = request.form.get('dm_message', Config.DM_MESSAGE)
        Config.DEFAULT_LINK = request.form.get('default_link', Config.DEFAULT_LINK)
        
        # Save configuration changes to persist across restarts
        Config.save_runtime_config()
        
        flash("Settings updated successfully!", 'success')
        
        return redirect('/manage_keywords')
        
    except Exception as e:
        logging.error(f"Error updating keywords: {e}")
        flash(f"Error updating settings: {e}", 'error')
        return redirect('/manage_keywords')

@app.route('/debug')
def debug_page():
    """Debug page to help troubleshoot configuration issues"""
    try:
        # Check Instagram login status
        login_issues = []
        if not Config.INSTAGRAM_SESSION_ID:
            login_issues.append("No Instagram session ID configured")
        elif len(Config.INSTAGRAM_SESSION_ID) < 20:
            login_issues.append("Instagram session ID appears too short")
        
        # Check keyword issues
        keyword_issues = []
        if not Config.KEYWORDS:
            keyword_issues.append("No keywords configured")
        
        # Check post issues
        post_issues = []
        if not Config.MONITOR_ALL_POSTS and not Config.SPECIFIC_POST_IDS:
            post_issues.append("❌ No posts being monitored - set MONITOR_ALL_POSTS=True or select specific posts")
        
        # Overall status
        if login_issues or keyword_issues or post_issues:
            config_status = "warning"
            status_message = "Configuration has issues"
        else:
            config_status = "success" 
            status_message = "Configuration looks good"
        
        debug_info = {
            'config_status': config_status,
            'status_message': status_message,
            'login_issues': login_issues,
            'keyword_issues': keyword_issues,
            'post_issues': post_issues,
            'config': {
                'instagram_username': Config.INSTAGRAM_USERNAME,
                'has_session_id': bool(Config.INSTAGRAM_SESSION_ID),
                'session_id_preview': (Config.INSTAGRAM_SESSION_ID[:20] + "...") if Config.INSTAGRAM_SESSION_ID else None,
                'keywords': Config.KEYWORDS,
                'monitor_all_posts': Config.MONITOR_ALL_POSTS,
                'specific_post_ids': Config.SPECIFIC_POST_IDS,
                'dm_message': Config.DM_MESSAGE,
                'default_link': Config.DEFAULT_LINK,
                'check_interval': Config.CHECK_INTERVAL
            }
        }
        
        return render_template('debug.html', debug=debug_info, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Debug page error: {e}")
        return f"Debug error: {e}", 500

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Update general settings like check interval"""
    try:
        # Update check interval
        check_interval = int(request.form.get('check_interval', Config.CHECK_INTERVAL))
        if check_interval != Config.CHECK_INTERVAL:
            old_interval = Config.CHECK_INTERVAL
            Config.CHECK_INTERVAL = check_interval
            
            # Restart scheduler with new interval if bot is running
            if bot_status['running']:
                stop_scheduler()
                time.sleep(1)  # Small delay
                start_scheduler()
                flash(f'Check interval updated from {old_interval}s to {check_interval}s and scheduler restarted', 'success')
            else:
                flash(f'Check interval updated from {old_interval}s to {check_interval}s', 'success')
        
        # Update other settings if provided
        if 'max_posts_to_check' in request.form:
            Config.MAX_POSTS_TO_CHECK = int(request.form.get('max_posts_to_check', Config.MAX_POSTS_TO_CHECK))
        
        # Save all settings
        Config.save_runtime_config()
        
        return redirect(request.referrer or url_for('dashboard'))
        
    except Exception as e:
        logging.error(f"Error updating settings: {e}")
        flash(f"Error updating settings: {e}", 'error')
        return redirect(request.referrer or url_for('dashboard'))

@app.route('/settings')
def settings_page():
    """General settings page"""
    try:
        settings_data = {
            'check_interval': Config.CHECK_INTERVAL,
            'max_posts_to_check': Config.MAX_POSTS_TO_CHECK,
            'dm_message': Config.DM_MESSAGE,
            'default_link': Config.DEFAULT_LINK,
        }
        
        return render_template('settings.html', settings=settings_data, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Settings page error: {e}")
        flash(f'Error loading settings: {str(e)}', 'error')
        return render_template('settings.html', settings={}, bot_status=bot_status)

@app.route('/instagram_login')
def instagram_login_page():
    """Instagram login credentials management page (MANUAL METHOD)"""
    try:
        login_data = {
            'username': Config.INSTAGRAM_USERNAME,
            'has_session_id': bool(Config.INSTAGRAM_SESSION_ID),
            'session_id_preview': (Config.INSTAGRAM_SESSION_ID[:20] + "...") if Config.INSTAGRAM_SESSION_ID else None,
        }
        
        return render_template('instagram_login_manual.html', login=login_data, bot_status=bot_status)
        
    except Exception as e:
        logging.error(f"Instagram login page error: {e}")
        flash(f'Error loading Instagram login: {str(e)}', 'error')
        return render_template('instagram_login_manual.html', login={}, bot_status=bot_status)

@app.route('/instagram-login-pro')
def instagram_login_pro_page():
    """Professional Instagram login page with REAL OAuth"""
    # Pass Instagram App ID to template for OAuth URL generation
    return render_template('instagram_login.html', instagram_app_id=Config.INSTAGRAM_APP_ID)

@app.route('/auth/instagram')
def auth_instagram():
    """Start Instagram Business OAuth flow"""
    try:
        # Check if Instagram App credentials are configured
        if not Config.INSTAGRAM_APP_ID or not Config.INSTAGRAM_APP_SECRET:
            flash('Instagram Business App credentials not configured. Please set INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET environment variables.', 'error')
            return redirect(url_for('instagram_login_pro_page'))
        
        # Generate secure state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        session['oauth_start_time'] = datetime.now().isoformat()
        
        # Instagram Business Login OAuth URL
        redirect_uri = urllib.parse.quote(request.url_root + 'auth/instagram/callback', safe='')
        scope = urllib.parse.quote('instagram_business_basic,instagram_business_manage_messages', safe='')
        
        oauth_url = (
            f"https://www.instagram.com/oauth/authorize?"
            f"client_id={Config.INSTAGRAM_APP_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"state={state}"
        )
        
        logging.info(f"Starting Instagram OAuth flow with redirect URI: {redirect_uri}")
        return redirect(oauth_url)
        
    except Exception as e:
        logging.error(f"OAuth start error: {e}")
        flash(f'Failed to start Instagram authentication: {str(e)}', 'error')
        return redirect(url_for('instagram_login_pro_page'))

@app.route('/auth/instagram/callback')
def auth_instagram_callback():
    """Handle Instagram Business OAuth callback"""
    try:
        # Get authorization code and state from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        # Handle OAuth errors
        if error:
            error_description = request.args.get('error_description', 'Unknown error')
            logging.error(f"Instagram OAuth error: {error} - {error_description}")
            flash(f'Instagram authentication failed: {error_description}', 'error')
            return redirect(url_for('instagram_login_pro_page'))
        
        # Verify state parameter for security
        if not state or state != session.get('oauth_state'):
            logging.error("Invalid OAuth state parameter")
            flash('Invalid authentication state. Please try again.', 'error')
            return redirect(url_for('instagram_login_pro_page'))
        
        if not code:
            flash('No authorization code received from Instagram.', 'error')
            return redirect(url_for('instagram_login_pro_page'))
        
        # Exchange authorization code for access token
        token_url = "https://api.instagram.com/oauth/access_token"
        token_data = {
            'client_id': Config.INSTAGRAM_APP_ID,
            'client_secret': Config.INSTAGRAM_APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': request.url_root + 'auth/instagram/callback',
            'code': code
        }
        
        logging.info("Exchanging authorization code for access token...")
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            logging.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            flash('Failed to exchange authorization code for access token.', 'error')
            return redirect(url_for('instagram_login_pro_page'))
        
        token_json = token_response.json()
        
        if 'error' in token_json:
            logging.error(f"Token exchange error: {token_json}")
            flash(f'Token exchange failed: {token_json.get("error_message", "Unknown error")}', 'error')
            return redirect(url_for('instagram_login_pro_page'))
        
        # Extract token data
        access_token = token_json['data'][0]['access_token']
        user_id = token_json['data'][0]['user_id']
        permissions = token_json['data'][0]['permissions']
        
        logging.info(f"Successfully obtained access token for user ID: {user_id}")
        logging.info(f"Granted permissions: {permissions}")
        
        # Exchange short-lived token for long-lived token (60 days)
        long_lived_url = "https://graph.instagram.com/access_token"
        long_lived_params = {
            'grant_type': 'ig_exchange_token',
            'client_secret': Config.INSTAGRAM_APP_SECRET,
            'access_token': access_token
        }
        
        logging.info("Exchanging for long-lived access token...")
        long_lived_response = requests.get(long_lived_url, params=long_lived_params)
        
        if long_lived_response.status_code == 200:
            long_lived_json = long_lived_response.json()
            if 'access_token' in long_lived_json:
                access_token = long_lived_json['access_token']
                expires_in = long_lived_json.get('expires_in', 5184000)  # 60 days default
                logging.info(f"Successfully obtained long-lived token (expires in {expires_in} seconds)")
            else:
                logging.warning("Failed to get long-lived token, using short-lived token")
        else:
            logging.warning(f"Long-lived token exchange failed: {long_lived_response.status_code}")
        
        # Save credentials to configuration
        Config.INSTAGRAM_ACCESS_TOKEN = access_token
        Config.INSTAGRAM_USER_ID = user_id
        Config.save_runtime_config()
        
        # Clear OAuth session data
        session.pop('oauth_state', None)
        session.pop('oauth_start_time', None)
        
        # Test the token by making a simple API call
        test_url = f"https://graph.instagram.com/v21.0/{user_id}"
        test_params = {
            'fields': 'id,username,account_type',
            'access_token': access_token
        }
        
        test_response = requests.get(test_url, params=test_params)
        if test_response.status_code == 200:
            user_info = test_response.json()
            username = user_info.get('username', 'Unknown')
            account_type = user_info.get('account_type', 'Unknown')
            
            logging.info(f"Token validation successful - Username: {username}, Account Type: {account_type}")
            flash(f'✅ Instagram Business authentication successful! Connected as @{username} ({account_type})', 'success')
        else:
            logging.warning(f"Token validation failed: {test_response.status_code}")
            flash('✅ Instagram authentication successful, but unable to validate account details.', 'success')
        
        # Reset bot to use new authentication method if it exists
        global bot
        if bot:
            bot.logged_in = False
            bot.last_login_check = None
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logging.error(f"OAuth callback error: {e}")
        flash(f'OAuth authentication failed: {str(e)}', 'error')
        return redirect(url_for('instagram_login_pro_page'))

@app.route('/update_instagram_login', methods=['POST'])
def update_instagram_login():
    """Update Instagram login credentials (manual method)"""
    try:
        # Update session ID
        session_id = request.form.get('session_id', '').strip()
        if session_id:
            Config.INSTAGRAM_SESSION_ID = session_id
            flash('✅ Instagram session ID updated successfully!', 'success')
            
            # Force re-login on next bot cycle
            global bot
            if bot:
                bot.logged_in = False
                bot.last_login_check = None
                
        else:
            flash('❌ Session ID cannot be empty', 'error')
            return redirect('/instagram_login')
        
        # Save configuration changes to persist across restarts
        Config.save_runtime_config()
        
        return redirect('/instagram_login')
        
    except Exception as e:
        logging.error(f"Error updating Instagram login: {e}")
        flash(f"Error updating login: {e}", 'error')
        return redirect('/instagram_login')

if __name__ == '__main__':
    # Load runtime configuration on startup
    print("🔧 Loading runtime configuration...")
    Config.load_runtime_config()
    
    # Initialize on startup
    print("🤖 Initializing Instagram bot...")
    init_bot()
    
    # Check if running in production
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting web application on port {port}")
    print(f"📍 Debug mode: {debug}")
    print(f"⏱️  Check interval: {Config.CHECK_INTERVAL} seconds")
    print(f"📊 Max posts to check: {Config.MAX_POSTS_TO_CHECK}")
    print(f"🔗 Default link: {Config.DEFAULT_LINK}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 