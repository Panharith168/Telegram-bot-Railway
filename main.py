#!/usr/bin/env python3
"""
Telegram Payment Tracking Bot

A bot that automatically extracts and sums payment amounts from chat messages
with support for multiple currencies (USD and Cambodian Riel).
"""

import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.background import BackgroundScheduler

from bot_handlers import setup_handlers
from currency_extractor import reset_totals
from database import get_database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def health_check():
    """Periodic health check for 24/7 monitoring"""
    try:
        # Test database connection
        db = get_database()
        db.connect()
        logger.info(f"✅ Bot health check passed - {datetime.now()}")
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")

def main():
    """Main function to initialize and run the Telegram bot."""
    # Load environment variables
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    logger.info("Starting Payment Tracking Bot...")
    
    try:
        # Create application
        app = ApplicationBuilder().token(bot_token).build()
        
        # Setup message and command handlers
        setup_handlers(app)
        
        # Setup daily reset scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            reset_totals, 
            'cron', 
            hour=0, 
            minute=0,
            id='daily_reset'
        )
        # Add health check every 30 minutes for 24/7 monitoring
        scheduler.add_job(
            health_check,
            'interval',
            minutes=30,
            id='health_check'
        )
        scheduler.start()
        logger.info("Daily reset scheduler started (midnight UTC)")
        logger.info("Health check scheduler started (every 30 minutes)")
        
        # Start the bot
        logger.info("Bot is running and listening for messages...")
        app.run_polling(allowed_updates=['message'])
        
    except Exception as e:
        logger.error(f"Critical error starting bot: {e}")
        sys.exit(1)
    finally:
        if 'scheduler' in locals():
            scheduler.shutdown()
            logger.info("Scheduler shutdown complete")

if __name__ == "__main__":
    main()
