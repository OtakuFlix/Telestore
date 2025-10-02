# ==================== DEPLOYMENT_GUIDE.md ====================
# Koyeb Deployment Guide

## Step-by-Step Instructions

### 1. Prepare Your Repository

Ensure these files are in your repository:
- `Dockerfile`
- `requirements.txt`
- `main.py`
- All Python modules (bot/, api/, database/)
- `.dockerignore`

**DO NOT commit**:
- `.env` file (contains secrets)
- `*.session` files
- `__pycache__/` directories

### 2. Create Koyeb Account

1. Go to https://www.koyeb.com/
2. Sign up (GitHub login recommended)
3. Verify your email

### 3. Create MongoDB Atlas Database

1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster (M0)
3. Create database user with password
4. Whitelist all IPs: `0.0.0.0/0` (for Koyeb access)
5. Get connection string from "Connect" button

### 4. Get Telegram Credentials

**API Credentials**:
1. Visit https://my.telegram.org
2. Login → API Development Tools
3. Create app → Get `api_id` and `api_hash`

**Bot Token**:
1. Open Telegram → @BotFather
2. Send `/newbot`
3. Follow prompts → Get bot token

### 5. Deploy to Koyeb

#### Option A: From GitHub (Recommended)

1. **Connect GitHub**:
   - In Koyeb dashboard → "Create Service"
   - Choose "GitHub"
   - Authorize Koyeb to access your repo
   - Select your repository

2. **Configure Build**:
   - Build method: `Dockerfile`
   - Dockerfile path: `./Dockerfile`
   - Build context: `/`

3. **Set Environment Variables**:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB=telestore
   BASE_APP_URL=https://your-app-name.koyeb.app
   PORT=8000
   ```

4. **Configure Service**:
   - Region: Choose closest to you
   - Instance type: Free (Eco)
   - Port: 8000
   - Health check path: `/health`

5. **Deploy**:
   - Click "Deploy"
   - Wait for build and deployment (3-5 minutes)

6. **Update BASE_APP_URL**:
   - After first deployment, copy your Koyeb URL
   - Update `BASE_APP_URL` environment variable
   - Redeploy the service

#### Option B: From Docker Hub

1. **Build and Push Image**:
```bash
docker build -t your-username/telestore-bot .
docker push your-username/telestore-bot
```

2. **Deploy on Koyeb**:
   - Create Service → Docker
   - Image: `your-username/telestore-bot`
   - Configure as above

### 6. Verify Deployment

1. **Check Logs**:
   - Koyeb dashboard → Your service → Logs
   - Look for: `Bot started successfully: @YourBotName`

2. **Test Bot**:
   - Open Telegram
   - Search for your bot
   - Send `/start`
   - Should receive welcome message

3. **Test API**:
   - Visit: `https://your-app.koyeb.app/health`
   - Should return: `{"status":"healthy"}`

### 7. Common Issues & Solutions

**Bot not responding**:
- Check logs for errors
- Verify `BOT_TOKEN` is correct
- Ensure no webhook is set (bot uses long polling)

**MongoDB connection error**:
- Verify connection string format
- Check database user permissions
- Ensure IP whitelist includes `0.0.0.0/0`

**Files not streaming**:
- Verify `BASE_APP_URL` matches your Koyeb URL
- Check if bot has access to Telegram API

**Build fails**:
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check build logs for specific errors

### 8. Update Deployment

**Automatic** (GitHub connected):
- Push to main branch
- Koyeb auto-deploys

**Manual**:
- Koyeb dashboard → Service → Redeploy

### 9. Environment Variables Reference

```bash
# Required
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456:ABC-DEFghIJKlmNO
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=telestore

# Important
BASE_APP_URL=https://your-app.koyeb.app

# Optional (defaults shown)
PORT=8000
```

### 10. Monitoring

**Health Check**:
- Endpoint: `/health`
- Koyeb checks every 30s

**Logs**:
- Real-time in Koyeb dashboard
- Shows bot activity and errors

**Metrics**:
- Koyeb provides CPU, memory, bandwidth stats

### 11. Scaling

**Free Tier**:
- 1 service
- 512MB RAM
- Sufficient for small-medium usage

**Upgrade** (if needed):
- More services
- Higher resources
- Custom domains

### 12. Security Best Practices

1. **Never commit secrets**:
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Use strong passwords**:
   - MongoDB users
   - Admin panels (if added)

3. **Regular updates**:
   - Keep dependencies updated
   - Monitor security advisories

4. **Backup database**:
   - MongoDB Atlas provides automatic backups
   - Consider additional backups for critical data

### 13. Getting Your App URL

After deployment:
1. Koyeb dashboard → Your service
2. Copy the URL (format: `https://app-name-org.koyeb.app`)
3. Update `BASE_APP_URL` environment variable
4. Redeploy

### 14. Testing Locally Before Deploy

```bash
# Set environment variables
export API_ID=your_id
export API_HASH=your_hash
export BOT_TOKEN=your_token
export MONGODB_URI=your_mongodb_uri
export MONGODB_DB=telestore
export BASE_APP_URL=http://localhost:8000

# Run
python main.py
```

Open http://localhost:8000/health to verify.

## Support

- Koyeb Docs: https://www.koyeb.com/docs
- Telegram Bot API: https://core.telegram.org/bots/api
- Pyrogram Docs: https://docs.pyrogram.org

## Next Steps

After successful deployment:
1. Create folders via bot
2. Upload test files
3. Verify streaming works
4. Share links with users
5. Monitor usage and performance