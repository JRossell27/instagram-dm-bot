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
            minutes=Config.CHECK_INTERVAL,
            id='bot_cycle'
        )
        scheduler.start()
        bot_status['running'] = True
        bot_status['next_run'] = datetime.now() + timedelta(minutes=Config.CHECK_INTERVAL)
        logging.info(f"Scheduler started - running every {Config.CHECK_INTERVAL} minutes")
        
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
    
    return render_template('config.html', config=config_data)

@app.route('/posts')
def posts_page():
    """Posts selection page"""
    try:
        if not bot or not bot.logged_in:
            if not init_bot():
                flash(f'Failed to connect to Instagram: {bot_status["error_message"]}', 'error')
                return render_template('posts.html', posts=[])
        
        posts = bot.get_recent_posts(15)  # Get more posts for selection
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
        
        return render_template('posts.html', posts=posts_data)
        
    except Exception as e:
        logging.error(f"Posts page error: {e}")
        flash(f'Error loading posts: {str(e)}', 'error')
        return render_template('posts.html', posts=[])

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
        
        return render_template('logs.html', logs=log_entries)
        
    except Exception as e:
        logging.error(f"Logs page error: {e}")
        flash(f'Error loading logs: {str(e)}', 'error')
        return render_template('logs.html', logs=[])

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

if __name__ == '__main__':
    # Initialize on startup
    init_bot()
    
    # Start in development mode
    app.run(host='0.0.0.0', port=5000, debug=True) 