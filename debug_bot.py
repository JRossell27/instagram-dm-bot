#!/usr/bin/env python3
"""Debug script to check Instagram bot configuration and status"""

import os
from config import Config
from instagram_bot import InstagramBot
from database import Database

def debug_bot():
    print("🔍 Instagram DM Bot Debug Information")
    print("="*50)
    
    # Check configuration
    print("📝 CONFIGURATION:")
    print(f"Keywords: {Config.KEYWORDS}")
    print(f"Monitor All Posts: {Config.MONITOR_ALL_POSTS}")
    print(f"Specific Post IDs: {Config.SPECIFIC_POST_IDS}")
    print(f"Required Hashtags: {Config.REQUIRED_HASHTAGS}")
    print(f"Required Caption Words: {Config.REQUIRED_CAPTION_WORDS}")
    print(f"Max Post Age (days): {Config.MAX_POST_AGE_DAYS}")
    print(f"Check Interval: {Config.CHECK_INTERVAL} minutes")
    print(f"DM Message: {Config.DM_MESSAGE[:50]}...")
    print(f"Default Link: {Config.DEFAULT_LINK}")
    
    print("\n🤖 BOT STATUS:")
    try:
        bot = InstagramBot()
        if bot.login():
            print("✅ Login: Successful")
            print(f"✅ Username: @{bot.username}")
            
            # Check recent posts
            print("\n📸 RECENT POSTS (first 5):")
            posts = bot.get_recent_posts(5)
            if posts:
                for i, post in enumerate(posts[:5], 1):
                    is_monitored = bot.should_monitor_post(post)
                    caption_preview = (post.caption_text[:50] + "...") if post.caption_text else "No caption"
                    print(f"  {i}. {post.code} - {post.taken_at.strftime('%Y-%m-%d %H:%M')}")
                    print(f"     Monitored: {'✅ YES' if is_monitored else '❌ NO'}")
                    print(f"     Caption: {caption_preview}")
                    
                    if is_monitored:
                        # Check comments on this post
                        try:
                            comments = bot.client.media_comments(post.id)
                            print(f"     Comments: {len(comments)} found")
                            for comment in comments[-3:]:  # Last 3 comments
                                keyword = bot.check_comment_for_keywords(comment.text)
                                print(f"       @{comment.user.username}: {comment.text[:30]}{'...' if len(comment.text) > 30 else ''}")
                                if keyword:
                                    print(f"         🎯 MATCHES KEYWORD: '{keyword}'")
                                else:
                                    print(f"         ❌ No keyword match")
                        except Exception as e:
                            print(f"     Error getting comments: {e}")
                    print()
            else:
                print("  ❌ No posts found")
                
        else:
            print("❌ Login: Failed")
            
    except Exception as e:
        print(f"❌ Bot Error: {e}")
    
    # Check database
    print("\n💾 DATABASE STATUS:")
    try:
        db = Database()
        recent_comments = db.get_recent_processed_comments(5)
        if recent_comments:
            print("Recent processed comments:")
            for comment in recent_comments:
                print(f"  @{comment[0]} - '{comment[1]}' - {comment[2]}")
        else:
            print("  No processed comments found")
    except Exception as e:
        print(f"❌ Database Error: {e}")
    
    print("\n🔧 TROUBLESHOOTING:")
    issues_found = []
    
    if not Config.MONITOR_ALL_POSTS and not Config.SPECIFIC_POST_IDS:
        issues_found.append("❌ No posts being monitored (MONITOR_ALL_POSTS=False and SPECIFIC_POST_IDS is empty)")
    
    if not Config.KEYWORDS:
        issues_found.append("❌ No keywords configured")
        
    if Config.DEFAULT_LINK == "https://your-website.com":
        issues_found.append("⚠️  Default link not customized")
    
    if issues_found:
        for issue in issues_found:
            print(issue)
        print("\n💡 SOLUTIONS:")
        if not Config.MONITOR_ALL_POSTS and not Config.SPECIFIC_POST_IDS:
            print("1. Go to website → 'Manage Posts' → Select posts to monitor")
            print("2. OR set MONITOR_ALL_POSTS = True in config.py")
    else:
        print("✅ Configuration looks good!")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    debug_bot() 