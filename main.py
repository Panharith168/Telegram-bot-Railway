"""
Telegram Payment Tracking Bot - Ultra Simple Railway Version

Minimal implementation to avoid Railway crashes.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Ultra simple main function for Railway."""
    logger.info("=== STARTING BOT ===")
    
    # Check environment
    bot_token = os.getenv('BOT_TOKEN')
    database_url = os.getenv('DATABASE_URL')
    
    logger.info(f"BOT_TOKEN: {'Present' if bot_token else 'Missing'}")
    logger.info(f"DATABASE_URL: {'Present' if database_url else 'Missing'}")
    
    if not bot_token:
        logger.error("BOT_TOKEN missing")
        return
    
    if not database_url:
        logger.error("DATABASE_URL missing")
        return
    
    try:
        # Test database first
        logger.info("Testing database...")
        from database_simple import get_database
        db = get_database()
        logger.info("Database connection OK")
        
        # Import and start bot
        logger.info("Starting bot...")
        from telegram.ext import Application
        from bot_handlers import setup_handlers
        
        app = Application.builder().token(bot_token).build()
        setup_handlers(app)
        
        logger.info("Bot configured, starting polling...")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()