#!/usr/bin/env python3
"""
Telegram Payment Tracking Bot

A comprehensive Telegram bot that automatically extracts and tracks payment amounts 
from chat messages with persistent PostgreSQL database storage, multi-currency support, 
and Excel export functionality.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('payment_bot.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to initialize and run the Telegram bot."""
    logger.info("Starting Telegram Payment Tracking Bot...")
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        from database import PaymentDatabase
        db = PaymentDatabase()
        await db.initialize()
        logger.info("Database initialized successfully")
        
        # Create application
        logger.info("Creating Telegram application...")
        application = Application.builder().token(bot_token).build()
        
        # Setup handlers
        from handlers import setup_handlers
        setup_handlers(application)
        logger.info("Handlers configured successfully")
        
        # Start the bot
        logger.info("Starting bot polling...")
        await application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())