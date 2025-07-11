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
        # Test database first with multiple attempts
        logger.info("Testing database connection...")
        
        db_attempts = 0
        max_attempts = 3
        db = None
        
        while db_attempts < max_attempts:
            try:
                from database import PaymentDatabase
                db = PaymentDatabase()
                logger.info("Database connection successful!")
                break
            except Exception as db_error:
                db_attempts += 1
                logger.warning(f"Database attempt {db_attempts}/{max_attempts} failed: {db_error}")
                if db_attempts >= max_attempts:
                    logger.error("Database connection failed after all attempts")
                    raise
                import time
                time.sleep(2)  # Wait 2 seconds before retry
        
        # Import and start bot
        logger.info("Starting Telegram bot...")
        from telegram.ext import Application
        from bot_handlers import setup_handlers
        
        app = Application.builder().token(bot_token).build()
        setup_handlers(app)
        
        logger.info("Bot configured successfully, starting polling...")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to continue without database for debugging
        logger.info("Attempting to start bot without database...")
        try:
            from telegram.ext import Application
            app = Application.builder().token(bot_token).build()
            
            # Add minimal handler
            async def error_handler(update, context):
                await update.message.reply_text("Bot is starting up, please try again in a moment...")
            
            from telegram.ext import MessageHandler, filters
            app.add_handler(MessageHandler(filters.TEXT, error_handler))
            
            logger.info("Emergency bot mode starting...")
            app.run_polling(drop_pending_updates=True)
        except Exception as final_error:
            logger.error(f"Complete failure: {final_error}")
            raise

if __name__ == "__main__":
    main()