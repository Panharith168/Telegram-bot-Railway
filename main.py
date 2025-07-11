"""
Telegram Payment Tracking Bot - Railway Fixed Version

A bot that tracks payment amounts via manual commands with persistent database storage.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to stdout for Railway
    ]
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return False
    
    # Check database credentials
    database_url = os.getenv('DATABASE_URL')
    pghost = os.getenv('PGHOST')
    
    if not database_url and not pghost:
        logger.error("No database credentials found")
        return False
    
    logger.info("Environment validation passed")
    return True

async def health_check():
    """Simple health check for Railway monitoring."""
    try:
        # Test database connection
        from database import get_database
        db = get_database()
        logger.info("Health check passed - database connection OK")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def main():
    """Main function to initialize and run the Telegram bot."""
    logger.info("Starting Telegram Payment Tracking Bot")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed - exiting")
        sys.exit(1)
    
    try:
        # Import after environment validation
        from telegram.ext import Application
        from bot_handlers import setup_handlers
        
        # Get bot token
        bot_token = os.getenv('BOT_TOKEN')
        logger.info("Initializing Telegram bot application")
        
        # Create application with explicit settings for Railway
        application = (
            Application.builder()
            .token(bot_token)
            .concurrent_updates(True)
            .build()
        )
        
        # Setup all command handlers
        setup_handlers(application)
        logger.info("Bot handlers configured successfully")
        
        # Test database connection before starting
        logger.info("Testing database connection...")
        asyncio.run(health_check())
        
        # Start the bot
        logger.info("Starting bot polling...")
        application.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True,  # Clear any pending updates
            close_loop=False
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()