#!/bin/bash

echo "Starting TeleStore Bot..."

# Create logs directory
mkdir -p logs

# Start the application
python main.py 2>&1 | tee logs/app.log

# ==================== COMPLETE INSTALLATION GUIDE ====================

cat << 'GUIDE'

╔════════════════════════════════════════════════════════════╗
║         TELESTORE BOT - COMPLETE SETUP GUIDE              ║
╔════════════════════════════════════════════════════════════╗

📋 PREREQUISITES:
─────────────────
1. Python 3.11+ installed
2. Git installed
3. Telegram account
4. MongoDB Atlas account (free tier)

🔧 LOCAL DEVELOPMENT SETUP:
───────────────────────────

Step 1: Clone/Create Project
────────────────────────────
mkdir telestore-bot
cd telestore-bot

Step 2: Create Project Structure
─────────────────────────────────
Create all directories:
  mkdir -p api/routes bot/handlers database

Create __init__.py files:
  touch api/__init__.py
  touch api/routes/__init__.py
  touch bot/__init__.py
  touch bot/handlers/__init__.py
  touch database/__init__.py

Step 3: Create Files
────────────────────
Copy all provided code files:
  - main.py
  - config.py
  - requirements.txt
  - Dockerfile
  - .env.example
  - .gitignore
  - .dockerignore
  
And all module files:
  - api/app.py
  - api/utils.py
  - api/routes/stream.py
  - api/routes/download.py
  - bot/client.py
  - bot/keyboards.py
  - bot/handlers/commands.py
  - bot/handlers/callbacks.py
  - bot/handlers/media.py
  - database/connection.py
  - database/models.py
  - database/operations.py

Step 4: Setup Environment
──────────────────────────
bash setup.sh

Or manually:
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt

Step 5: Configure .env
──────────────────────
cp .env.example .env
nano .env  # or use your preferred editor

Fill in:
  API_ID=12345678
  API_HASH=your_hash_here
  BOT_TOKEN=123456:ABCdef...
  MONGODB_URI=mongodb+srv://...
  MONGODB_DB=telestore
  BASE_APP_URL=http://localhost:8000
  PORT=8000

Step 6: Get Credentials
────────────────────────

A. Telegram API (API_ID & API_HASH):
   1. Go to https://my.telegram.org
   2. Login with phone number
   3. Click "API Development Tools"
   4. Create new application
   5. Copy api_id and api_hash

B. Bot Token:
   1. Open Telegram
   2. Search @BotFather
   3. Send: /newbot
   4. Follow prompts
   5. Copy bot token

C. MongoDB:
   1. Go to https://mongodb.com/cloud/atlas
   2. Sign up / Login
   3. Create free cluster (M0)
   4. Database Access → Add user (username + password)
   5. Network Access → Add IP: 0.0.0.0/0
   6. Connect → Drivers → Copy connection string
   7. Replace <password> in connection string

Step 7: Run Bot
────────────────
python main.py

You should see:
  [STARTUP] Starting Telegram bot...
  [STARTUP] Bot started successfully: @YourBot
  INFO: Uvicorn running on http://0.0.0.0:8000

Step 8: Test
────────────
1. Open Telegram → Find your bot
2. Send: /start
3. Should get welcome message
4. Try: /newfolder Test
5. Add files to folder

Step 9: Test Streaming
──────────────────────
1. Upload a video file
2. Get file link
3. Open in browser: http://localhost:8000/fileId
4. Video should play

🐳 DOCKER DEPLOYMENT:
─────────────────────

Local Docker Test:
  docker build -t telestore-bot .
  docker run -p 8000:8000 --env-file .env telestore-bot

Docker Compose:
  docker-compose up -d

☁️ KOYEB DEPLOYMENT:
────────────────────

Step 1: Push to GitHub
───────────────────────
git init
git add .
git commit -m "Initial commit"
git remote add origin your-github-repo
git push -u origin main

Step 2: Connect to Koyeb
─────────────────────────
1. Go to https://koyeb.com
2. Sign up / Login
3. Create Service → GitHub
4. Authorize GitHub → Select repo

Step 3: Configure
─────────────────
Build:
  - Method: Dockerfile
  - Path: ./Dockerfile

Ports:
  - Port: 8000
  - Protocol: HTTP

Environment Variables:
  API_ID=your_value
  API_HASH=your_value
  BOT_TOKEN=your_value
  MONGODB_URI=your_value
  MONGODB_DB=telestore
  BASE_APP_URL=https://your-app.koyeb.app
  PORT=8000

Step 4: Deploy
──────────────
Click "Deploy" → Wait 3-5 minutes

Step 5: Update URL
───────────────────
After deployment:
1. Copy Koyeb app URL
2. Update BASE_APP_URL in environment
3. Redeploy

Step 6: Verify
──────────────
1. Check logs in Koyeb
2. Test bot in Telegram
3. Visit: https://your-app.koyeb.app/health

🎯 USAGE EXAMPLES:
──────────────────

Create Folder:
  /newfolder My Movies

Add Files:
  1. /myfolders
  2. Click folder
  3. Click "Add Files"
  4. Send videos
  5. /done

Get Links:
  1. Click file in folder
  2. Copy watch/download links

URLs:
  Stream: https://your-domain.com/abc123xyz
  Download: https://your-domain.com/dl/abc123xyz
  Player: https://your-domain.com/watch/abc123xyz

🔍 TROUBLESHOOTING:
───────────────────

Bot not responding:
  ❌ Check BOT_TOKEN is correct
  ❌ Verify bot is running (check logs)
  ❌ Ensure no webhook set

MongoDB errors:
  ❌ Check connection string format
  ❌ Verify user has read/write permissions
  ❌ Ensure IP 0.0.0.0/0 whitelisted

Files not streaming:
  ❌ Check BASE_APP_URL is correct
  ❌ Verify file exists in database
  ❌ Check Telegram file_id is valid

Build fails:
  ❌ Check Python version (need 3.11+)
  ❌ Verify all files are present
  ❌ Check requirements.txt

📊 MONITORING:
──────────────

Logs:
  - Check Koyeb dashboard
  - Look for errors in startup
  - Monitor user activity

Health Check:
  - Endpoint: /health
  - Should return: {"status":"healthy"}

Database:
  - MongoDB Atlas → Metrics
  - Check connection count
  - Monitor storage usage

🔒 SECURITY:
────────────

✅ DO:
  - Use environment variables
  - Keep .env private
  - Regular backups
  - Monitor logs

❌ DON'T:
  - Commit .env to git
  - Share bot token
  - Use weak passwords
  - Expose admin endpoints

📚 ADDITIONAL RESOURCES:
────────────────────────

Documentation:
  - Pyrogram: https://docs.pyrogram.org
  - FastAPI: https://fastapi.tiangolo.com
  - MongoDB: https://docs.mongodb.com
  - Koyeb: https://koyeb.com/docs

Support:
  - GitHub Issues
  - Telegram: @your_support_bot
  - Email: support@example.com

🎉 YOU'RE READY!
────────────────

Your bot is now set up and ready to use!

Test checklist:
  ☐ Bot responds to /start
  ☐ Can create folders
  ☐ Can upload files
  ☐ Files stream correctly
  ☐ Downloads work
  ☐ Embedded player works

Need help? Check the docs or open an issue!

GUIDE