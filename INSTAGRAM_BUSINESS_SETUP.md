# Instagram Business API Setup Guide

## Overview

This bot now supports **official Instagram Business OAuth authentication** like Sprout Social, HootSuite, and other professional tools. This replaces the previous screen scraping method with Instagram's official Graph API.

## Prerequisites

### 1. Instagram Business or Creator Account
- You **must** have an Instagram Business or Creator account
- Personal accounts are **not supported** by Instagram's Business API
- Convert your account at: Instagram Settings → Account → Switch to Professional Account

### 2. Facebook Developer Account
- Create a free account at [developers.facebook.com](https://developers.facebook.com)
- No Facebook Page required with the new Instagram API (as of July 2024)

## Setup Steps

### Step 1: Create Instagram App

1. Go to [Meta Developer Console](https://developers.facebook.com/apps/)
2. Click **"Create App"**
3. Select **"Consumer"** as the app type
4. Fill in app details:
   - App Name: `[Your Company] Instagram DM Bot`
   - Contact Email: Your email
   - App Purpose: Business automation

### Step 2: Add Instagram Product

1. In your app dashboard, click **"+ Add Product"**
2. Find **"Instagram Platform"** and click **"Set Up"**
3. Choose **"Instagram API with Instagram Login"**

### Step 3: Configure Instagram Business Login

1. In the Instagram Platform section, go to **"API setup with Instagram login"**
2. Under **"3. Set up Instagram business login"**, configure:
   - **Valid OAuth Redirect URIs**: Add your bot's callback URL:
     ```
     https://your-app-domain.com/auth/instagram/callback
     ```
     For local development:
     ```
     http://localhost:5000/auth/instagram/callback
     ```

### Step 4: Get App Credentials

1. In **"Business login settings"**, copy:
   - **Instagram App ID** 
   - **Instagram App Secret**

### Step 5: Set Environment Variables

Add these to your environment (Render, Heroku, etc.) or `.env` file:

```bash
# Instagram Business API OAuth Credentials
INSTAGRAM_APP_ID=your_app_id_here
INSTAGRAM_APP_SECRET=your_app_secret_here

# Optional: Generate a random secret for OAuth state validation
OAUTH_STATE_SECRET=your_random_secret_here
```

### Step 6: Request Advanced Access (If Needed)

**For testing with your own account**: Standard Access is sufficient

**For production with other users' accounts**: 
1. Go to **App Review** in your app dashboard
2. Request **Advanced Access** for:
   - `instagram_business_basic`
   - `instagram_business_manage_messages`
3. Submit for review with use case explanation

## Using the Bot

### 1. OAuth Authentication

1. Go to your bot's web interface
2. Click **"Instagram Business Login"** 
3. Click **"Connect Instagram Business Account"**
4. You'll be redirected to Instagram's official login page
5. Log in with your Instagram Business/Creator account
6. Authorize the permissions
7. You'll be redirected back with a success message

### 2. Token Management

- **Access tokens are automatically managed**
- **Tokens last 60 days** and auto-refresh
- No manual session ID extraction needed
- Works with 2FA accounts seamlessly

## Advantages of Business API

### ✅ Reliability
- **No more 401 errors** from session expiration
- **No bot detection issues**
- Official API with guaranteed uptime

### ✅ Security  
- **OAuth 2.0 standard** - same as Sprout Social
- **No password sharing** required
- **Automatic token refresh**

### ✅ Compliance
- **Instagram-approved method** for automation
- **Rate limiting handled automatically**
- **Follows platform best practices**

### ✅ Features
- **Real-time messaging** via webhooks (future)
- **Message type support** (text, images, reactions)
- **Conversation management**
- **Analytics and insights**

## Troubleshooting

### "Instagram Business App credentials not configured"
- Ensure `INSTAGRAM_APP_ID` and `INSTAGRAM_APP_SECRET` are set
- Restart your application after setting variables

### "Failed to exchange authorization code"
- Check that your **redirect URI** exactly matches what's configured in Meta Dashboard
- Ensure app is not in **Development Mode** for production use

### "No authorization code received"
- User may have denied permissions
- Check that account is Business/Creator (not Personal)

### "Token validation failed"
- Account may not have required permissions
- Try refreshing the access token
- Ensure account is properly linked to a Facebook Page (for messaging)

## Migration from Screen Scraping

### Automatic Detection
The bot will automatically:
1. **Try Business API first** if credentials are configured
2. **Fall back to screen scraping** if Business API fails
3. **Show clear status** of which method is active

### Benefits of Migration
- **24/7 reliability** without session expiration
- **No more manual session ID updates**
- **Professional-grade authentication**
- **Future-proof** as Instagram phases out unofficial access

## Rate Limits

Instagram Business API has generous rate limits:
- **200 API calls per hour** per access token
- **Messaging limits**: 1000 messages per day initially
- **Comments**: 100 reads per hour per endpoint

## Support

### Instagram Business API Documentation
- [Instagram Platform Overview](https://developers.facebook.com/docs/instagram-platform/)
- [Business Login Flow](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login/)
- [Messaging API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/)

### Common Issues
- **Account Type**: Must be Business/Creator, not Personal
- **Permissions**: Ensure `instagram_business_manage_messages` is granted
- **App Review**: May be required for production usage with external accounts

## Next Steps

1. **Set up credentials** following this guide
2. **Test OAuth flow** with your Business account
3. **Verify DM automation** works with official API
4. **Phase out manual session method** once confirmed working

The bot maintains **backward compatibility** so you can test the Business API while keeping your current setup as backup. 