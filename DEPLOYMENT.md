# Instagram DM Bot - Web Deployment Guide

This guide explains how to deploy your Instagram DM Bot as a web application on various cloud platforms, so your team can access it from anywhere without needing to keep your computer running.

## 🌟 Benefits of Web Deployment

- ✅ **24/7 Operation**: Runs continuously without your computer
- ✅ **Team Access**: Multiple team members can manage the bot
- ✅ **Professional Interface**: Beautiful web dashboard
- ✅ **Real-time Monitoring**: Live stats and logs
- ✅ **Easy Configuration**: Web-based settings management
- ✅ **Scalable**: Can handle multiple Instagram accounts

## 🚀 Quick Start Options

### Option 1: Railway (Recommended - Easiest)

Railway is the easiest platform with a generous free tier.

1. **Create Railway Account**: Visit [railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub account
3. **Deploy**: 
   - Click "Deploy from GitHub repo"
   - Select your bot repository
   - Railway auto-detects the Python app

4. **Set Environment Variables** in Railway dashboard:
   ```
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   SECRET_KEY=your-random-secret-key-here
   ```

5. **Access Your Bot**: Railway provides a URL like `https://your-app.railway.app`

### Option 2: Heroku

Heroku is reliable with good documentation.

1. **Install Heroku CLI**: Download from [heroku.com/cli](https://heroku.com/cli)

2. **Create Heroku App**:
   ```bash
   heroku create your-instagram-bot
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set INSTAGRAM_USERNAME=your_username
   heroku config:set INSTAGRAM_PASSWORD=your_password
   heroku config:set SECRET_KEY=your-random-secret-key
   ```

4. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

5. **Open App**: `heroku open`

### Option 3: Render

Render offers simple deployment with automatic HTTPS.

1. **Create Render Account**: Visit [render.com](https://render.com)
2. **Connect Repository**: Link your GitHub repo
3. **Create Web Service**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn web_app:app`
4. **Set Environment Variables** in Render dashboard
5. **Deploy**: Render auto-deploys from GitHub

### Option 4: Google Cloud Run

For more advanced users who want Google Cloud integration.

1. **Install Google Cloud CLI**
2. **Build Container**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/instagram-bot
   ```
3. **Deploy**:
   ```bash
   gcloud run deploy --image gcr.io/PROJECT-ID/instagram-bot --platform managed
   ```

## 📋 Environment Variables Setup

All platforms require these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `INSTAGRAM_USERNAME` | Your Instagram username | `your_username` |
| `INSTAGRAM_PASSWORD` | Your Instagram password | `your_password` |
| `SECRET_KEY` | Random string for session security | `abc123xyz789` |

### Generating a Secret Key

```python
import secrets
print(secrets.token_hex(16))
```

## 🛠️ Platform-Specific Instructions

### Railway Detailed Setup

1. **Fork the Repository** to your GitHub account
2. **Sign up for Railway** using your GitHub account
3. **Deploy from GitHub**:
   - Click "Deploy from GitHub repo"
   - Select your forked repository
   - Railway automatically detects it's a Python app
4. **Configure Environment Variables**:
   - Go to your project dashboard
   - Click "Variables" tab
   - Add the required environment variables
5. **Deploy**: Railway builds and deploys automatically
6. **Access**: Get your app URL from the Railway dashboard

### Heroku Detailed Setup

1. **Prepare Your Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   heroku git:remote -a your-app-name
   ```

3. **Configure Environment**:
   ```bash
   heroku config:set INSTAGRAM_USERNAME=your_username
   heroku config:set INSTAGRAM_PASSWORD=your_password
   heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Monitor Logs**:
   ```bash
   heroku logs --tail
   ```

## 🔒 Security Best Practices

### Credentials Management
- ✅ Use environment variables (never commit passwords)
- ✅ Generate strong secret keys
- ✅ Regularly rotate passwords
- ✅ Use Instagram App Passwords if available

### Access Control
- ✅ Use HTTPS (enabled by default on most platforms)
- ✅ Consider adding basic authentication for team access
- ✅ Monitor logs for suspicious activity
- ✅ Keep the platform updated

## 📊 Post-Deployment Setup

### 1. Initial Configuration
After deployment, visit your app URL and:
- Configure which posts to monitor
- Set up keywords and DM messages
- Test with a single run

### 2. Team Access
Share the app URL with your social media team:
- Dashboard: Monitor bot activity
- Configuration: View current settings
- Posts: See which posts are being monitored
- Logs: Debug issues and view activity

### 3. Ongoing Management
- **Monitor regularly**: Check the dashboard for activity
- **Update configuration**: Edit `config.py` and redeploy as needed
- **Check logs**: Review for errors or issues
- **Scale if needed**: Upgrade hosting plan for high traffic

## 🔧 Troubleshooting

### Common Deployment Issues

**Build Failures:**
- Ensure `requirements.txt` is complete
- Check Python version compatibility
- Verify all files are committed to Git

**Environment Variable Issues:**
- Double-check variable names (case-sensitive)
- Ensure no extra spaces in values
- Regenerate secret key if needed

**Instagram Connection Issues:**
- Verify credentials are correct
- Check if account has 2FA (may need app password)
- Monitor Instagram's rate limits

**Performance Issues:**
- Upgrade to paid hosting plan if needed
- Optimize check intervals in config
- Monitor memory usage in platform dashboard

### Platform-Specific Troubleshooting

**Railway:**
- Check build logs in Railway dashboard
- Ensure PORT environment variable is not set manually
- Railway auto-assigns ports

**Heroku:**
- Use `heroku logs --tail` for real-time logs
- Check dyno status: `heroku ps`
- Restart if needed: `heroku restart`

**Render:**
- Check build logs in Render dashboard
- Ensure health checks are passing
- Monitor resource usage

## 💰 Cost Considerations

### Free Tiers
- **Railway**: 500 hours/month free
- **Heroku**: 1000 hours/month free (with credit card)
- **Render**: 750 hours/month free

### Paid Plans (for 24/7 operation)
- **Railway**: $5+/month
- **Heroku**: $7+/month  
- **Render**: $7+/month

### Cost Optimization Tips
- Use free tiers for testing
- Optimize check intervals to reduce resource usage
- Monitor usage in platform dashboards
- Upgrade only when needed

## 🔄 Updates and Maintenance

### Updating the Bot
1. **Edit configuration** in `config.py`
2. **Commit changes** to Git
3. **Deploy update**:
   - Railway: Auto-deploys from GitHub
   - Heroku: `git push heroku main`
   - Render: Auto-deploys from GitHub

### Monitoring Health
- Check dashboard regularly
- Review logs for errors
- Monitor Instagram rate limits
- Verify DMs are being sent

### Backup and Recovery
- Database is SQLite (included in deployment)
- Regular log monitoring
- Keep copy of configuration settings
- Document any custom modifications

## 🎯 Success Checklist

After deployment, verify:
- ✅ Web dashboard loads correctly
- ✅ Bot can connect to Instagram
- ✅ Configuration displays properly
- ✅ Posts are being detected and filtered correctly
- ✅ Test run completes successfully
- ✅ Logs show normal activity
- ✅ Team members can access the dashboard

## 📞 Support Resources

### Platform Documentation
- [Railway Docs](https://docs.railway.app/)
- [Heroku Docs](https://devcenter.heroku.com/)
- [Render Docs](https://render.com/docs)

### Bot-Specific Help
- Check the dashboard logs for detailed error messages
- Review configuration settings
- Test Instagram connectivity
- Monitor rate limiting messages

---

**Need Help?** Check the logs in your web dashboard first - they contain detailed information about any issues the bot encounters. 