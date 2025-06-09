# 🔧 Emergency Session ID Refresh Guide

## 🚨 Problem: Instagram is detecting automation and blocking your requests

### Step 1: Clear Instagram Data
1. **Open Chrome/Firefox in INCOGNITO/PRIVATE mode**
2. **Go to instagram.com** 
3. **Clear all Instagram cookies** (important!)

### Step 2: Manual Login (Critical for avoiding detection)
1. **Login manually** to your @ppv_com account
2. **Browse Instagram normally** for 2-3 minutes:
   - Like a few posts
   - View some stories  
   - Check your feed
   - Act like a real human

### Step 3: Get Fresh Session ID
1. **Press F12** (Developer Tools)
2. **Go to Application tab** → **Cookies** → **instagram.com**
3. **Find 'sessionid' cookie**
4. **Copy the ENTIRE value** (it's very long!)

### Step 4: Update in Bot
1. **Go to your bot's web interface**
2. **Settings** → **Instagram Login**
3. **Paste the new session ID**
4. **Save changes**

### Step 5: Test Gradually
1. **Wait 10-15 minutes** before testing
2. **Start with a single test run**
3. **Don't run continuously immediately**

## ⚠️ Additional Steps to Avoid Detection:

### Change Your Bot Behavior:
1. **Increase check interval** to 60-120 seconds (instead of 30)
2. **Monitor fewer posts** initially
3. **Reduce keywords** to 1-2 most important ones

### Account Hygiene:
1. **Use Instagram manually** from the same IP occasionally
2. **Don't run 24/7** initially - build up gradually
3. **Monitor success rate** - if DMs keep failing, pause for a few hours

## 🎯 Expected Results:
- ✅ No more JSONDecodeError messages
- ✅ Successful post fetching
- ✅ Proper user ID resolution
- ✅ Stable session lasting days/weeks instead of hours

## 🔴 If Problems Persist:
1. **Wait 6-24 hours** before trying again
2. **Try from a different IP address**
3. **Consider using a VPN**
4. **Contact Instagram support** if your account seems restricted 