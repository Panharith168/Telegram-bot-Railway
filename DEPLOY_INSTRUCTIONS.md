# Deploy Your Bot to Railway (24/7 Hosting)

## Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Click "Login with GitHub"
3. Allow Railway to access your GitHub account

## Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose "Create new repo" or import existing one

## Step 3: Upload Bot Files
Upload all these files to your GitHub repository:
- `main.py`
- `bot_handlers.py` 
- `currency_extractor.py`
- `database.py`
- `dependencies.txt`
- `railway.json`
- `Procfile`
- `runtime.txt`
- `.env.example`

## Step 4: Configure Environment Variables
In Railway dashboard:
1. Go to "Variables" tab
2. Add these variables:
   - `BOT_TOKEN` = `7694341937:AAEhTyiNWyX3mLfQdWnfnYBdjMcMWcS57ZM`
   - `DATABASE_URL` = (Railway will auto-generate this)

## Step 5: Add PostgreSQL Database
1. Click "Add Service"
2. Select "PostgreSQL"
3. Railway will automatically connect it to your bot

## Step 6: Deploy
1. Railway will automatically deploy your bot
2. Check the "Logs" tab to see if it's running
3. You should see "Bot is running and listening for messages..."

## Alternative: One-Click Deploy
Use this button to deploy directly:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/python-telegram-bot)

## After Deployment
1. Your bot will be running 24/7 automatically
2. Go to @BotFather on Telegram
3. Send `/mybots` → Select your bot → "Bot Settings" → "Group Privacy" → "Disable"
4. Add your bot to a group and test with messages like "I paid $50"

## Monitoring
- Check Railway dashboard for logs and health status
- Bot automatically restarts if it crashes
- Health checks run every 30 minutes
- View logs in Railway console

Your bot will now run continuously without needing your computer to be on!