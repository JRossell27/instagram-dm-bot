# Instagram 2FA Backup Code Setup Guide

Since Instagram no longer allows easily disabling 2FA, you can use backup codes to authenticate your bot.

## ⚠️ Important Note About Backup Codes

Instagram backup codes sometimes don't work with automated tools like ours. If you're getting "Please check the security code and try again", this is normal. Here are your options:

### Option 1: Generate Fresh Backup Codes
1. **Open Instagram app**
2. **Go to Settings → Security → Two-Factor Authentication**
3. **Tap "Recovery Codes"**
4. **Generate NEW backup codes** (this invalidates old ones)
5. **Use a fresh, unused backup code**

### Option 2: Use App-Based 2FA (Recommended)
If backup codes keep failing, you can set up app-based 2FA:

1. **Open Instagram app**
2. **Go to Settings → Security → Two-Factor Authentication**
3. **Add "Authentication App"** (Google Authenticator, Authy, etc.)
4. **Get the TOTP code from your authenticator app**
5. **Use the TOTP code instead of backup code**

For TOTP codes, they change every 30 seconds, so you'd need to:
- Generate a fresh code from your authenticator app
- Quickly add it to Render environment variables
- Test immediately

## 🔑 Current Setup Instructions

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

## 🔧 Troubleshooting

**"Please check the security code and try again"**:
- This means Instagram rejected the backup code
- Generate NEW backup codes (step-by-step above)
- Use a completely fresh, unused backup code
- Remove ALL spaces: `9307 4281` → `93074281`

**"2FA code invalid or expired"**:
- Generate a new backup code from Instagram
- Update `INSTAGRAM_2FA_CODE` in Render
- Make sure you haven't used this backup code before

**"Rate limit reached"**:
- Wait a few hours before trying again
- Instagram may temporarily limit login attempts

**If backup codes keep failing**:
- Switch to authenticator app method (Option 2 above)
- Contact us for help setting up alternative authentication

## 🔄 Session Management

- Once logged in successfully, the bot saves a session file
- Future logins will use the saved session (no 2FA needed)
- If session expires, it will use your backup code again
- Sessions typically last several weeks

## 📱 Alternative: Using TOTP Codes

If backup codes don't work, you can use time-based codes:

1. **Set up Google Authenticator or similar app**
2. **Generate a 6-digit code from the app**
3. **Quickly update `INSTAGRAM_2FA_CODE` in Render**
4. **Test within 30 seconds** (codes expire quickly)

This is more reliable but requires manual intervention every time the session expires. 