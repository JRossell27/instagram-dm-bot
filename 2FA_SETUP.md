# Instagram 2FA (Two-Factor Authentication) Setup Guide

If your Instagram account has 2FA enabled, you have several options to make the bot work:

## Option 1: Use App-Specific Password (Recommended if Available)

1. **Go to Instagram Settings**:
   - Open Instagram app or website
   - Go to Settings → Security → Two-Factor Authentication
   - Look for "App Passwords" or "Application-specific passwords"

2. **Generate App Password**:
   - If available, create a new app password for "Instagram DM Bot"
   - Use this password instead of your regular password in Render

3. **Update Render Environment Variables**:
   - Go to your Render dashboard
   - Update `INSTAGRAM_PASSWORD` with the app-specific password
   - Keep `INSTAGRAM_USERNAME` the same

## Option 2: Temporarily Disable 2FA (Not Recommended)

⚠️ **Security Warning**: Only do this temporarily and re-enable 2FA after setup

1. **Disable 2FA**:
   - Go to Instagram Settings → Security → Two-Factor Authentication
   - Turn off 2FA temporarily

2. **Test the Bot**:
   - Try the bot login on Render
   - Once working, the bot will save a session file

3. **Re-enable 2FA**:
   - Turn 2FA back on in Instagram settings
   - The bot should continue working with the saved session

## Option 3: Manual Session Setup (Advanced)

If you're comfortable with technical setup:

1. **Run Bot Locally First**:
   - Clone the repository to your computer
   - Install dependencies: `pip install -r requirements.txt`
   - Set up `.env` file with your credentials
   - Run `python main.py once` and complete 2FA manually
   - This creates a `session.json` file

2. **Upload Session to Render**:
   - This is more complex and requires additional setup

## Option 4: Use a Dedicated Instagram Account

**Best Practice for Business Use**:

1. **Create a new Instagram account** specifically for automation
2. **Don't enable 2FA** on this automation account
3. **Use this account's credentials** in the bot
4. **Follow/connect this account** to your main business account

## Checking Your Current Status

The bot will now give you specific error messages:

- **"Instagram 2FA is enabled"** → Use one of the options above
- **"Invalid username or password"** → Check your credentials in Render
- **"Instagram requires verification"** → Log into Instagram manually first
- **"Rate limit reached"** → Wait a few hours and try again

## Next Steps

1. **Choose an option above** that works for your situation
2. **Update your Render environment variables** if needed
3. **Test the bot** by clicking "Test Run" in the dashboard
4. **Check the logs** for detailed error messages

---

**Need Help?** Check the bot logs in your web dashboard for specific error messages and guidance. 