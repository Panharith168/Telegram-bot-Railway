"""
Telegram Payment Tracking Bot - Railway Crash Fix

Fixes the event loop and database connection issues on Railway.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return False
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    logger.info("Environment validation passed")
    return True

def test_database():
    """Test database connection."""
    try:
        from database import get_database
        db = get_database()
        logger.info("Database connection test passed")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def main():
    """Main function - Railway crash fix."""
    logger.info("Starting Telegram Payment Tracking Bot (Railway Fix)")
    
    # Validate environment first
    if not validate_environment():
        logger.error("Environment validation failed")
        sys.exit(1)
    
    # Test database connection
    if not test_database():
        logger.error("Database test failed")
        sys.exit(1)
    
    try:
        # Import bot modules after validation
        from telegram.ext import Application
        from bot_handlers import setup_handlers
        
        bot_token = os.getenv('BOT_TOKEN')
        logger.info("Creating Telegram application")
        
        # Create application with Railway-specific settings
        application = Application.builder().token(bot_token).build()
        
        # Setup handlers
        setup_handlers(application)
        logger.info("Bot handlers configured")
        
        # Start bot with Railway-compatible settings
        logger.info("Starting bot polling...")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message'],
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we have an event loop for Railway
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    main()