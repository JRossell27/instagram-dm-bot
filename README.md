# Instagram DM Bot

An automated Instagram bot that monitors comments on your posts for specific keywords and sends direct messages with links to users who comment those keywords.

## Features

- 🔍 **Keyword Monitoring**: Watches for specific keywords in comments on your posts
- 📱 **Auto DM**: Automatically sends personalized DMs with links
- 📊 **Tracking**: Prevents duplicate messages and tracks all activity  
- ⚙️ **Configurable**: Easy to customize keywords, messages, and links
- 🛡️ **Safe**: Built-in rate limiting and error handling
- 🎯 **Selective Monitoring**: Choose exactly which posts to monitor

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Create a `.env` file with your Instagram credentials:
```
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

### 3. Run Setup

```bash
python setup.py
```

### 4. Choose Posts to Monitor

**Important**: By default, the bot will NOT monitor any posts. You must configure which posts to monitor.

## Post Selection Options

### Option 1: Monitor ALL Posts
```python
# In config.py
MONITOR_ALL_POSTS = True
```

### Option 2: Specific Posts Only
```python
# In config.py
SPECIFIC_POST_IDS = [
    "ABC123DEF",  # Post ID from Instagram URL
    "XYZ789GHI", 
]
```

To find your post IDs:
```bash
python main.py posts
```

### Option 3: Hashtag Filtering
```python
# In config.py
REQUIRED_HASHTAGS = [
    "#dmbot",
    "#automate",
]
```

### Option 4: Caption Word Filtering  
```python
# In config.py
REQUIRED_CAPTION_WORDS = [
    "dm for details",
    "link in bio",
    "interested", 
]
```

### Option 5: Age-Based Filtering
```python
# In config.py
MAX_POST_AGE_DAYS = 7  # Only monitor posts from last 7 days
```

### Option 6: Posts with Links Only
```python
# In config.py
ONLY_POSTS_WITH_LINKS = True  # Only monitor posts mentioning links
```

You can combine multiple filters for precise targeting!

## Usage

### Start the Bot
```bash
python main.py
```

### Test Run (Single Check)
```bash
python main.py once
```

### View Statistics
```bash
python main.py stats
```

### List Your Recent Posts
```bash
python main.py posts
```

### Setup Help
```bash
python setup.py posts  # Show post selection guide
```

## Configuration

### Keywords
Default keywords that trigger DMs:
- "dm me"
- "send link" 
- "info"
- "details"
- "interested"

### DM Message Template
```
Hi! Thanks for your interest! 

Here's the link you requested: {link}

Let me know if you have any questions!
```

### Full Customization
All settings can be modified in `config.py`:

```python
# Keywords to monitor
KEYWORDS = [
    'dm me',
    'send link',
    'your custom keyword'
]

# Your custom message
DM_MESSAGE = """Your custom message here with {link}"""

# Your link
DEFAULT_LINK = "https://your-website.com"

# Post filtering
MONITOR_ALL_POSTS = False
SPECIFIC_POST_IDS = ["ABC123", "XYZ789"]
REQUIRED_HASHTAGS = ["#dmbot"]
REQUIRED_CAPTION_WORDS = ["dm for info"]
MAX_POST_AGE_DAYS = 7
```

## How It Works

1. **Post Selection**: Bot checks which posts match your filtering criteria
2. **Monitoring**: Scans comments on selected posts every 5 minutes
3. **Detection**: Identifies comments containing your keywords
4. **Response**: Sends automated DM with your message and link
5. **Tracking**: Records all activity to prevent duplicates

## Commands Reference

| Command | Description |
|---------|-------------|
| `python main.py` | Start continuous monitoring |
| `python main.py once` | Run single check (testing) |
| `python main.py stats` | View statistics and config |
| `python main.py posts` | List recent posts for selection |
| `python setup.py` | Initial setup and configuration |
| `python setup.py posts` | Post selection guide |

## Examples

### Monitor specific posts only:
1. Run `python main.py posts`
2. Copy post IDs you want to monitor
3. Edit config.py:
```python
SPECIFIC_POST_IDS = [
    "CAbCdEfGhI",  # Your first post
    "XyZaBcDeFg",  # Your second post
]
```

### Monitor posts with specific hashtags:
```python
REQUIRED_HASHTAGS = [
    "#dmbot",      # Tag posts you want monitored
    "#linkdrop",   # with these hashtags
]
```

### Monitor recent posts only:
```python
MAX_POST_AGE_DAYS = 3  # Only posts from last 3 days
REQUIRED_CAPTION_WORDS = ["dm me"]  # That mention "dm me"
```

## Database

The bot uses SQLite to track:
- Processed comments (prevents duplicates)
- Sent DMs (for analytics)
- Activity timestamps

## Logs

Activity is logged to:
- `instagram_bot.log` (file)
- Console output

## Rate Limiting

Built-in protections:
- 2-second delay between DMs
- 1-second delay between post checks
- Automatic handling of Instagram rate limits

## Security Notes

- Store credentials securely in `.env` file
- Don't commit credentials to version control
- Monitor bot activity regularly
- Follow Instagram's Terms of Service

## Troubleshooting

### No Posts Being Monitored
- Check that at least one filter is configured
- Set `MONITOR_ALL_POSTS = True` to monitor everything
- Run `python main.py posts` to see available posts
- Check logs for filtering messages

### Login Issues
- Verify credentials in `.env`
- Check if account has 2FA enabled
- Try logging in manually first

### No Comments Detected
- Ensure keywords match exactly (case-insensitive)
- Check if posts have recent comments
- Verify bot has access to account

### DMs Not Sending  
- Check Instagram DM restrictions
- Verify recipient can receive DMs
- Monitor rate limiting messages

## Support

Check the logs for detailed error messages:
- `instagram_bot.log` for detailed logs
- Console output for real-time status

---

**Disclaimer**: This bot is for educational purposes. Ensure compliance with Instagram's Terms of Service and use responsibly. 