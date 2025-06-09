#!/usr/bin/env python3
import time
import schedule
import logging
from instagram_bot import InstagramBot
from config import Config

def main():
    """Main function to run the Instagram DM bot"""
    print("Instagram DM Bot Starting...")
    print("="*50)
    
    # Initialize bot
    bot = InstagramBot()
    
    # Initial login
    if not bot.login():
        print("Failed to login. Please check your credentials in .env file")
        return
    
    print(f"Bot is now monitoring for keywords: {', '.join(Config.KEYWORDS)}")
    print(f"Checking every {Config.CHECK_INTERVAL} seconds")
    
    # Show filtering status
    if Config.MONITOR_ALL_POSTS:
        print("📌 Monitoring: ALL posts")
    else:
        filters_active = []
        if Config.SPECIFIC_POST_IDS:
            filters_active.append(f"Specific posts ({len(Config.SPECIFIC_POST_IDS)})")
        if Config.REQUIRED_HASHTAGS:
            filters_active.append(f"Posts with hashtags: {', '.join(Config.REQUIRED_HASHTAGS)}")
        if Config.REQUIRED_CAPTION_WORDS:
            filters_active.append(f"Posts with phrases: {', '.join(Config.REQUIRED_CAPTION_WORDS)}")
        if Config.MAX_POST_AGE_DAYS:
            filters_active.append(f"Posts newer than {Config.MAX_POST_AGE_DAYS} days")
        if Config.ONLY_POSTS_WITH_LINKS:
            filters_active.append("Posts with links only")
        
        if filters_active:
            print("📌 Active filters:")
            for f in filters_active:
                print(f"   • {f}")
        else:
            print("⚠️  No filters active - will not monitor any posts")
            print("   Configure filters in config.py or set MONITOR_ALL_POSTS = True")
    
    print("Press Ctrl+C to stop")
    print("="*50)
    
    # Schedule the monitoring
    schedule.every(Config.CHECK_INTERVAL).seconds.do(bot.run_monitoring_cycle)
    
    # Run initial cycle
    bot.run_monitoring_cycle()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        logging.info("Bot stopped by user")

def run_once():
    """Run the bot once for testing"""
    bot = InstagramBot()
    if bot.login():
        bot.run_monitoring_cycle()
        
        # Show stats
        stats = bot.get_stats()
        print(f"\nRecent activity:")
        for comment in stats['recent_processed']:
            print(f"- @{comment[0]} (keyword: {comment[1]}) at {comment[2]}")

def show_stats():
    """Show bot statistics"""
    bot = InstagramBot()
    stats = bot.get_stats()
    
    print("Instagram DM Bot Statistics")
    print("="*30)
    print(f"Status: {'Online' if stats['logged_in'] else 'Offline'}")
    if stats['username']:
        print(f"Account: @{stats['username']}")
    
    print(f"\nMonitored Keywords: {', '.join(Config.KEYWORDS)}")
    print(f"Check Interval: {Config.CHECK_INTERVAL} seconds")
    
    # Show filtering configuration
    print(f"\nPost Filtering:")
    if Config.MONITOR_ALL_POSTS:
        print("  • Monitoring ALL posts")
    else:
        print("  • Selective monitoring enabled:")
        if Config.SPECIFIC_POST_IDS:
            print(f"    - Specific posts: {len(Config.SPECIFIC_POST_IDS)} configured")
        if Config.REQUIRED_HASHTAGS:
            print(f"    - Required hashtags: {', '.join(Config.REQUIRED_HASHTAGS)}")
        if Config.REQUIRED_CAPTION_WORDS:
            print(f"    - Required phrases: {', '.join(Config.REQUIRED_CAPTION_WORDS)}")
        if Config.MAX_POST_AGE_DAYS:
            print(f"    - Max age: {Config.MAX_POST_AGE_DAYS} days")
        if Config.ONLY_POSTS_WITH_LINKS:
            print("    - Posts with links only: Yes")
    
    print(f"\nRecent Processed Comments:")
    recent = stats['recent_processed']
    if recent:
        for comment in recent[:5]:
            print(f"  @{comment[0]} - '{comment[1]}' - {comment[2]}")
    else:
        print("  No recent activity")

def list_posts():
    """List recent posts for easy selection"""
    bot = InstagramBot()
    if bot.login():
        bot.list_recent_posts_for_selection()
        print("\nTo monitor specific posts, copy the Post IDs and add them to")
        print("the SPECIFIC_POST_IDS list in config.py")
        print("\nExample:")
        print("SPECIFIC_POST_IDS = [")
        print('    "ABC123DEF",  # Replace with actual post ID')
        print('    "XYZ789GHI",')
        print("]")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            run_once()
        elif sys.argv[1] == "stats":
            show_stats()
        elif sys.argv[1] == "posts" or sys.argv[1] == "list":
            list_posts()
        else:
            print("Usage: python main.py [once|stats|posts]")
            print("  once  - Run bot once for testing")
            print("  stats - Show bot statistics and configuration")
            print("  posts - List recent posts for selection")
    else:
        main() 