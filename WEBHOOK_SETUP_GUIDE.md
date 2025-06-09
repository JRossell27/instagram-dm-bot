# 🔔 Instagram Webhook Setup Guide - ManyChat Strategy

## Overview
Webhooks are **critical** for ManyChat-style automation. Instead of checking for new comments every few minutes (polling), webhooks notify your bot **instantly** when someone comments - enabling sub-second response times like ManyChat.

---

## 📋 Prerequisites

✅ **Before you start, ensure you have:**
- Instagram Business App created in Meta Developer Console
- Your Render app deployed and running
- Instagram Business account connected via OAuth
- App ID and App Secret configured

---

## 🚀 Step-by-Step Webhook Setup

### **Step 1: Access Meta Developer Console**

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **"My Apps"** in top-right corner
3. Select your Instagram Business App (App ID: `2574946899368966`)

### **Step 2: Navigate to Webhooks**

1. In your app dashboard, click **"Webhooks"** in the left sidebar
2. You'll see the webhooks configuration page

### **Step 3: Add Webhook URL**

1. Click **"Add Subscription"** or **"Edit Subscription"**
2. **Callback URL**: `https://instagram-dm-bot-tk4d.onrender.com/webhook/instagram`
3. **Verify Token**: Create a secure random string (save this!)
   ```
   Example: wh_verify_token_abc123_secure_random_string
   ```

### **Step 4: Configure Environment Variable**

Add the verify token to your Render environment variables:

1. Go to your Render dashboard
2. Select your app
3. Go to **Environment** tab
4. Add new variable:
   ```
   WEBHOOK_VERIFY_TOKEN=wh_verify_token_abc123_secure_random_string
   ```

### **Step 5: Subscribe to Instagram Events**

In the webhooks section, find **"Instagram"** and subscribe to:

✅ **Required Events:**
- `comments` - **CRITICAL for ManyChat strategy**
- `messages` - For DM responses (if available)

Click **"Subscribe"** for each event.

### **Step 6: Verify Webhook**

1. Meta will send a GET request to verify your webhook
2. Your bot will automatically respond with the challenge
3. You should see ✅ **"Verified"** status

---

## 🔧 Advanced Configuration

### **Step 7: Configure App Permissions**

Ensure your app has these permissions:
- `instagram_business_basic`
- `instagram_business_manage_messages`
- `instagram_business_manage_comments`

### **Step 8: Set Webhook Fields**

For Instagram subscriptions, configure these fields:
```
comments, messages, messaging_postbacks
```

---

## 🧪 Testing Your Webhook

### **Method 1: Test via Dashboard**

1. Go to your bot dashboard: `https://instagram-dm-bot-tk4d.onrender.com`
2. Navigate to webhook test section
3. Send test webhook data

### **Method 2: Manual Test**

Use curl to test webhook processing:

```bash
curl -X POST https://instagram-dm-bot-tk4d.onrender.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{
    "comment_text": "dm me the link please",
    "username": "testuser", 
    "user_id": "123456789"
  }'
```

### **Method 3: Real Comment Test**

1. Comment on one of your Instagram posts with: **"dm me"**
2. Check your logs for webhook notification
3. Verify bot processes the comment in real-time

---

## ✅ Verification Checklist

### **Webhook Status Check:**
- [ ] Webhook URL is verified in Meta Developer Console
- [ ] Status shows ✅ "Verified" 
- [ ] Subscribed to `comments` event
- [ ] Environment variable `WEBHOOK_VERIFY_TOKEN` is set
- [ ] Render app is running and accessible

### **Functional Test:**
- [ ] Test webhook endpoint responds correctly
- [ ] Real comments trigger webhook notifications
- [ ] Bot logs show incoming webhook data
- [ ] Direct DMs are sent for consent keywords
- [ ] Public replies sent for interest keywords

---

## 🚨 Troubleshooting

### **Problem: Webhook Verification Failed**

**Solution:**
1. Check `WEBHOOK_VERIFY_TOKEN` environment variable
2. Verify webhook URL is correct and accessible
3. Check Render app logs for errors

### **Problem: No Webhook Notifications**

**Solution:**
1. Verify Instagram account is connected via OAuth
2. Check if subscribed to `comments` event
3. Test with a real comment on your post
4. Check Meta Developer Console for webhook delivery logs

### **Problem: Webhook Receives Data But Bot Doesn't Process**

**Solution:**
1. Check bot logs for processing errors
2. Verify bot is logged in to Instagram Business API
3. Check database for processed comments table

### **Problem: SSL Certificate Error**

**Solution:**
1. Ensure your Render app has valid SSL certificate
2. Try accessing webhook URL directly in browser
3. Meta requires HTTPS for webhook URLs

---

## 📊 Monitoring Webhook Performance

### **Check Webhook Delivery:**

1. In Meta Developer Console → Webhooks
2. Click **"View Deliveries"** next to your webhook
3. See real-time delivery status and response codes

### **Expected Response Codes:**
- `200` - Webhook processed successfully
- `403` - Verification token mismatch
- `500` - Internal server error

### **Bot Logs to Monitor:**
```
✅ Instagram webhook verified successfully
🔔 Instagram webhook received: {...}
🎯 KEYWORD MATCH: 'dm me' from @username
✅ Direct message sent successfully to user 123456
```

---

## 🔥 Pro Tips for ManyChat-Level Performance

### **1. Optimize Response Time**
- Use background processing for heavy operations
- Keep webhook handler lightweight
- Return 200 status immediately

### **2. Handle High Volume**
- Implement request queuing for burst traffic
- Use database connection pooling
- Monitor memory usage

### **3. Error Recovery**
- Log all webhook failures
- Implement retry logic for failed DMs
- Monitor webhook delivery success rate

### **4. Security Best Practices**
- Validate webhook signature (if provided)
- Use secure verify tokens
- Monitor for suspicious activity

---

## 🎯 Expected Results

Once webhooks are properly configured, you should see:

- **⚡ Sub-second response times** (like ManyChat)
- **📈 Higher engagement rates** due to instant responses  
- **📊 Real-time analytics** in your dashboard
- **🔔 Instant notifications** when comments are posted
- **📩 Automatic DMs** for consent keywords

**Your bot will now respond as fast as ManyChat!** 🚀

---

## 📞 Need Help?

If you encounter issues:

1. **Check Render logs** for detailed error messages
2. **Verify Meta Developer Console** webhook status
3. **Test webhook endpoint** manually with curl
4. **Monitor bot dashboard** for real-time status

Remember: Webhooks are the **key difference** between a slow polling bot and a professional ManyChat-level automation system! 🔥 