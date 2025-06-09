# Instagram 2FA Backup Code Setup Guide

Since Instagram no longer allows easily disabling 2FA, you can use backup codes to authenticate your bot.

## 🔑 Using Your Backup Code

### Step 1: Add the 2FA Code to Render

1. **Go to your Render dashboard**
2. **Click on your instagram-dm-bot service**
3. **Go to the "Environment" tab**
4. **Add a new environment variable**:
   - **Key**: `INSTAGRAM_2FA_CODE`
   - **Value**: `93074281` (remove the space from your backup code)

### Step 2: Test the Bot

1. **Save the environment variable** in Render
2. **Wait for automatic redeploy** (1-2 minutes)
3. **Go to your bot dashboard**
4. **Click "Test Run"**
5. **Check logs** - should see "Successfully logged in to Instagram"

## 📱 Getting More Backup Codes

When your current backup code expires or gets used up:

1. **Open Instagram app**
2. **Go to Settings → Security → Two-Factor Authentication**
3. **Tap "Recovery Codes"**
4. **Generate new backup codes**
5. **Update the `INSTAGRAM_2FA_CODE` variable** in Render with a new code (remove spaces)

## 🔄 Session Management

- Once logged in successfully, the bot saves a session file
- Future logins will use the saved session (no 2FA needed)
- If session expires, it will use your backup code again
- Sessions typically last several weeks

## ⚠️ Important Notes

- **Remove spaces** from backup codes: `9307 4281` → `93074281`
- **Each backup code can only be used once**
- **Keep your backup codes secure** - don't share them
- **The bot will tell you** when a code is invalid or expired

## 🔧 Troubleshooting

**"2FA code invalid or expired"**:
- Generate a new backup code from Instagram
- Update `INSTAGRAM_2FA_CODE` in Render

**"Rate limit reached"**:
- Wait a few hours before trying again
- Instagram may temporarily limit login attempts

**"Session saved for future logins"**:
- ✅ Success! The bot is now logged in and will remember the session 