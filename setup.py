#!/usr/bin/env python3
import os
import shutil

def setup_bot():
    """Setup the Instagram DM bot"""
    print("Instagram DM Bot Setup")
    print("="*30)
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from template")
        else:
            # Create basic .env file
            with open('.env', 'w') as f:
                f.write('INSTAGRAM_USERNAME=your_username\n')
                f.write('INSTAGRAM_PASSWORD=your_password\n')
            print("✓ Created basic .env file")
    
    print("\n📝 Configuration Steps:")
    print("1. Edit the .env file with your Instagram credentials")
    print("2. Configure post filtering in config.py")
    print("3. Modify keywords in config.py if needed")
    print("4. Update the DM message template in config.py")
    print("5. Set your default link in config.py")
    
    print("\n🔧 Current Keywords:")
    from config import Config
    for i, keyword in enumerate(Config.KEYWORDS, 1):
        print(f"   {i}. '{keyword}'")
    
    print(f"\n📧 Current DM Message Template:")
    print(f"   {Config.DM_MESSAGE[:100]}...")
    
    print(f"\n🔗 Current Default Link:")
    print(f"   {Config.DEFAULT_LINK}")
    
    print(f"\n📌 Post Filtering Configuration:")
    if Config.MONITOR_ALL_POSTS:
        print("   Currently monitoring: ALL posts")
    else:
        print("   Currently monitoring: SELECTIVE posts")
        if Config.SPECIFIC_POST_IDS:
            print(f"   • Specific posts: {len(Config.SPECIFIC_POST_IDS)} configured")
        if Config.REQUIRED_HASHTAGS:
            print(f"   • Required hashtags: {', '.join(Config.REQUIRED_HASHTAGS)}")
        if Config.REQUIRED_CAPTION_WORDS:
            print(f"   • Required phrases: {', '.join(Config.REQUIRED_CAPTION_WORDS)}")
        if Config.MAX_POST_AGE_DAYS:
            print(f"   • Max post age: {Config.MAX_POST_AGE_DAYS} days")
        if not any([Config.SPECIFIC_POST_IDS, Config.REQUIRED_HASHTAGS, Config.REQUIRED_CAPTION_WORDS]):
            print("   ⚠️  No filters configured - bot won't monitor any posts!")
    
    print("\n🚀 Commands:")
    print("   python main.py       - Start the bot")
    print("   python main.py once  - Test run (single check)")
    print("   python main.py stats - View statistics")
    print("   python main.py posts - List your recent posts for selection")
    
    print("\n📋 Post Selection Options:")
    print("   1. Monitor ALL posts: Set MONITOR_ALL_POSTS = True")
    print("   2. Specific posts: Add post IDs to SPECIFIC_POST_IDS")
    print("   3. Hashtag filtering: Add hashtags to REQUIRED_HASHTAGS")
    print("   4. Caption filtering: Add phrases to REQUIRED_CAPTION_WORDS")
    print("   5. Age filtering: Set MAX_POST_AGE_DAYS")

def update_keywords():
    """Interactive keyword update"""
    from config import Config
    
    print("Current Keywords:")
    for i, keyword in enumerate(Config.KEYWORDS, 1):
        print(f"{i}. '{keyword}'")
    
    print("\nEnter new keywords (one per line, empty line to finish):")
    new_keywords = []
    while True:
        keyword = input("Keyword: ").strip()
        if not keyword:
            break
        new_keywords.append(keyword)
    
    if new_keywords:
        # Update config file
        config_content = open('config.py', 'r').read()
        
        # Replace KEYWORDS list
        keywords_str = ',\n        '.join([f"'{k}'" for k in new_keywords])
        new_keywords_section = f"KEYWORDS = [\n        {keywords_str}\n    ]"
        
        # This is a simple replacement - in production you'd want more robust parsing
        print("⚠️  Please manually update the KEYWORDS list in config.py")
        print("New keywords to add:")
        for keyword in new_keywords:
            print(f"  '{keyword}'")

def show_post_selection_help():
    """Show help for post selection"""
    print("Post Selection Guide")
    print("="*30)
    
    print("\n🎯 Option 1: Monitor ALL posts")
    print("   Set: MONITOR_ALL_POSTS = True")
    print("   Use when: You want the bot active on every post")
    
    print("\n🎯 Option 2: Specific post IDs")
    print("   Use: SPECIFIC_POST_IDS = ['ABC123', 'XYZ789']")
    print("   Use when: You want to select exact posts")
    print("   Tip: Run 'python main.py posts' to see your post IDs")
    
    print("\n🎯 Option 3: Hashtag filtering")
    print("   Use: REQUIRED_HASHTAGS = ['#dmbot', '#automate']") 
    print("   Use when: You tag certain posts for automation")
    
    print("\n🎯 Option 4: Caption word filtering")
    print("   Use: REQUIRED_CAPTION_WORDS = ['dm for details', 'link in bio']")
    print("   Use when: You want to match specific phrases")
    
    print("\n🎯 Option 5: Age filtering")
    print("   Use: MAX_POST_AGE_DAYS = 7")
    print("   Use when: You only want recent posts monitored")
    
    print("\n💡 Pro Tips:")
    print("   • Combine multiple filters for precise targeting")
    print("   • Test with 'python main.py once' before going live")
    print("   • Check logs to see which posts are being monitored")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "keywords":
            update_keywords()
        elif sys.argv[1] == "posts" or sys.argv[1] == "help":
            show_post_selection_help()
        else:
            print("Usage: python setup.py [keywords|posts]")
    else:
        setup_bot() 