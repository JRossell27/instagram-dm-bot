#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from instagram_bot import InstagramBot
from config import Config
from database import Database
import time

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
        debug_info = {
            'config': {
                'keywords': Config.KEYWORDS,
                'monitor_all_posts': Config.MONITOR_ALL_POSTS,
                'specific_post_ids': Config.SPECIFIC_POST_IDS,
                'required_hashtags': Config.REQUIRED_HASHTAGS,
                'required_caption_words': Config.REQUIRED_CAPTION_WORDS,
                'max_post_age_days': Config.MAX_POST_AGE_DAYS,
                'dm_message': Config.DM_MESSAGE,
                'default_link': Config.DEFAULT_LINK,
            },
            'bot_logged_in': bot and bot.logged_in,
            'runtime_config_exists': os.path.exists(Config.RUNTIME_CONFIG_FILE),
            'issues': []
        }
        
        # Check for common issues
        if not Config.MONITOR_ALL_POSTS and not Config.SPECIFIC_POST_IDS:
            debug_info['issues'].append("❌ No posts being monitored - set MONITOR_ALL_POSTS=True or select specific posts")
        
        if not Config.KEYWORDS:
            debug_info['issues'].append("❌ No keywords configured")
            
        if Config.DEFAULT_LINK == "https://your-website.com":
            debug_info['issues'].append("⚠️ Default link not customized")
            
        if not (bot and bot.logged_in):
            debug_info['issues'].append("❌ Bot not logged in to Instagram")
        
        # Try to get recent posts info if logged in
        if bot and bot.logged_in:
            try:
                recent_posts = bot.get_recent_posts(5)
                debug_info['recent_posts'] = []
                for post in recent_posts:
                    is_monitored = bot.should_monitor_post(post)
                    debug_info['recent_posts'].append({
                        'code': post.code,
                        'date': post.taken_at.strftime("%Y-%m-%d %H:%M"),
                        'caption_preview': (post.caption_text[:50] + "...") if post.caption_text else "No caption",
                        'is_monitored': is_monitored
                    })
            except Exception as e:
                debug_info['posts_error'] = str(e)
        
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