# Telegram Payment Tracking Bot - Final Deployment Package

## Files Included (8 files total):

1. **main.py** - Ultra-simple Railway-compatible main application
2. **database.py** - Railway-optimized PostgreSQL connection with SSL support
3. **bot_handlers.py** - All Telegram bot command handlers
4. **currency_extractor.py** - Currency detection and database operations
5. **requirements.txt** - Python dependencies with locked versions
6. **Procfile** - Railway deployment configuration
7. **runtime.txt** - Python version specification
8. **.env.example** - Environment variable template

## Deployment Instructions:

1. **Upload all 8 files** to your GitHub repository
2. **Replace any existing files** with the same names
3. **Environment Variables** (Railway dashboard):
   - `BOT_TOKEN` = `7694341937:AAEhTyiNWyX3mLfQdWnfnYBdjMcMWcS57ZM`
   - `DATABASE_URL` = (automatically provided by Railway)
4. **Railway auto-deploys** within 2-3 minutes

## Bot Commands:

- `/start` - Welcome message
- `/add $100` - Add USD payment
- `/add ៛25000` - Add KHR payment
- `/total` - Show today's totals
- `/week` - This week's totals
- `/month` - This month's totals
- `/year` - This year's totals
- `/export` - Export to Excel
- `/help` - Show all commands

## Features:

✅ **Command-only operation** - No automatic message processing
✅ **Railway-compatible** - Fixed all deployment issues
✅ **PostgreSQL database** - Persistent storage with SSL
✅ **Cambodia timezone** - Proper UTC+7 handling
✅ **Multi-currency support** - USD and Cambodian Riel
✅ **Excel export** - Payment data analysis
✅ **24/7 hosting** - Deployed on Railway platform

## Testing:

After deployment, test with:
1. `/total` - Should show $0.00 (new database)
2. `/add $100` - Add test payment
3. `/total` - Should show $100.00

Your bot will be accessible at: `@biomedpayment_bot`