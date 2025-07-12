"""
Telegram bot handlers

Handles all bot commands and automatic message processing for payment detection.
"""

import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, filters
)
from telegram.constants import ParseMode

from database import PaymentDatabase
from currency_detector import extract_amounts, test_detection

logger = logging.getLogger(__name__)

# Global database instance
db = PaymentDatabase()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    welcome_message = """
🤖 **Telegram Payment Tracking Bot**

Welcome! I automatically detect and track payment amounts from your messages.

**Supported Currencies:**
💵 USD: $10.50, $1,200.25
🏛️ Cambodian Riel: ៛25,000, ៛500,000

**Available Commands:**
/help - Show all commands
/total - Today's totals
/week - Weekly totals
/month - Monthly totals
/year - Yearly totals
/summary - Detailed daily summary
/export [period] - Export to Excel
/test <message> - Test payment detection

**Automatic Detection:**
Just send messages with payment amounts and I'll track them automatically!

Examples:
• "I paid $50 for lunch"
• "Received ៛100,000 payment"
• "Transfer $25.50"
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_message = """
📚 **Available Commands:**

**💰 Payment Tracking:**
/total - Show today's payment totals
/week - Show this week's totals
/month - Show this month's totals
/year - Show this year's totals
/summary - Detailed breakdown of today's payments

**📊 Data Export:**
/export - Export this month's data to Excel
/export week - Export this week's data
/export year - Export this year's data
/export all - Export all payment data

**🔍 Testing:**
/test <message> - Test payment detection on a message

**💡 How It Works:**
• Send any message containing payment amounts
• I automatically detect USD ($) and Riel (៛) amounts
• All payments are stored permanently
• View totals and export data anytime

**Supported Formats:**
• USD: $100, $50.25, 100$, "paid $25"
• KHR: ៛25000, ៛100,000, 25000៛, "received ៛50000"
    """
    
    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def total_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /total command."""
    try:
        chat_id = update.effective_chat.id
        usd_total, riel_total = await db.get_totals(chat_id, 'today')
        
        message = f"""
📊 **Today's Payment Totals**

💵 USD: ${usd_total:.2f}
🏛️ KHR: ៛{riel_total:,.0f}

Use /summary for detailed breakdown
        """
        
        await update.message.reply_text(
            message.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in total command: {e}")
        await update.message.reply_text("❌ Error retrieving totals. Please try again.")

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /week command."""
    try:
        chat_id = update.effective_chat.id
        usd_total, riel_total = await db.get_totals(chat_id, 'week')
        
        message = f"""
📊 **This Week's Payment Totals**

💵 USD: ${usd_total:.2f}
🏛️ KHR: ៛{riel_total:,.0f}

Last 7 days of payments
        """
        
        await update.message.reply_text(
            message.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in week command: {e}")
        await update.message.reply_text("❌ Error retrieving weekly totals. Please try again.")

async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /month command."""
    try:
        chat_id = update.effective_chat.id
        usd_total, riel_total = await db.get_totals(chat_id, 'month')
        
        message = f"""
📊 **This Month's Payment Totals**

💵 USD: ${usd_total:.2f}
🏛️ KHR: ៛{riel_total:,.0f}

Current month payments
        """
        
        await update.message.reply_text(
            message.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in month command: {e}")
        await update.message.reply_text("❌ Error retrieving monthly totals. Please try again.")

async def year_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /year command."""
    try:
        chat_id = update.effective_chat.id
        usd_total, riel_total = await db.get_totals(chat_id, 'year')
        
        message = f"""
📊 **This Year's Payment Totals**

💵 USD: ${usd_total:.2f}
🏛️ KHR: ៛{riel_total:,.0f}

Current year payments
        """
        
        await update.message.reply_text(
            message.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in year command: {e}")
        await update.message.reply_text("❌ Error retrieving yearly totals. Please try again.")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /summary command."""
    try:
        chat_id = update.effective_chat.id
        summary = await db.get_daily_summary(chat_id)
        
        message = f"""
📋 **Daily Summary - {summary['date']}**

**Totals:**
💵 USD: ${summary['usd_total']:.2f}
🏛️ KHR: ៛{summary['riel_total']:,.0f}

**Payments:** {summary['payment_count']} transactions
        """
        
        if summary['payments']:
            message += "\n\n**Recent Payments:**\n"
            for payment in summary['payments'][:5]:  # Show last 5
                time_str = payment['time'].strftime('%H:%M')
                user = payment['user'] or 'Unknown'
                usd = float(payment['usd'])
                riel = float(payment['riel'])
                
                if usd > 0:
                    message += f"• {time_str} - {user}: ${usd:.2f}\n"
                if riel > 0:
                    message += f"• {time_str} - {user}: ៛{riel:,.0f}\n"
        
        await update.message.reply_text(
            message.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in summary command: {e}")
        await update.message.reply_text("❌ Error retrieving summary. Please try again.")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command."""
    try:
        # Get period parameter
        period = 'month'  # default
        if context.args:
            period = context.args[0].lower()
            if period not in ['week', 'month', 'year', 'all']:
                await update.message.reply_text(
                    "❌ Invalid period. Use: week, month, year, or all"
                )
                return
        
        chat_id = update.effective_chat.id
        
        await update.message.reply_text("📊 Generating Excel export...")
        
        filename = await db.export_payments(chat_id, period)
        
        if filename:
            # Send the Excel file
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📊 Payment data export ({period})"
                )
            
            # Clean up file
            import os
            os.remove(filename)
        else:
            await update.message.reply_text(
                "❌ No payment data found for the specified period or export failed."
            )
        
    except Exception as e:
        logger.error(f"Error in export command: {e}")
        await update.message.reply_text("❌ Error generating export. Please try again.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /test command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /test <message>\n\nExample: /test I paid $50 for lunch"
        )
        return
    
    test_text = " ".join(context.args)
    result = test_detection(test_text)
    
    await update.message.reply_text(
        result,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages for automatic payment detection."""
    try:
        message_text = update.message.text
        if not message_text:
            return
        
        # Extract amounts
        usd_amount, riel_amount = extract_amounts(message_text)
        
        # Only process if we found payment amounts
        if usd_amount > 0 or riel_amount > 0:
            # Get user and chat info
            user_id = update.effective_user.id
            username = update.effective_user.username or update.effective_user.first_name or "Unknown"
            chat_id = update.effective_chat.id
            chat_title = getattr(update.effective_chat, 'title', 'Private Chat')
            
            # Save to database
            payment_id = await db.add_payment(
                user_id=user_id,
                username=username,
                chat_id=chat_id,
                chat_title=chat_title,
                message_text=message_text,
                usd_amount=usd_amount,
                riel_amount=riel_amount
            )
            
            # Send confirmation
            confirmation = "✅ **Payment Detected & Recorded**\n\n"
            if usd_amount > 0:
                confirmation += f"💵 USD: ${usd_amount:.2f}\n"
            if riel_amount > 0:
                confirmation += f"🏛️ KHR: ៛{riel_amount:,.0f}\n"
            confirmation += f"\nUse /total to see today's totals"
            
            await update.message.reply_text(
                confirmation,
                parse_mode=ParseMode.MARKDOWN
            )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        # Don't reply with error for automatic detection

def setup_handlers(application: Application) -> None:
    """Setup all command and message handlers."""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("total", total_command))
    application.add_handler(CommandHandler("week", week_command))
    application.add_handler(CommandHandler("month", month_command))
    application.add_handler(CommandHandler("year", year_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("test", test_command))
    
    # Message handler for automatic payment detection
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    logger.info("All handlers configured successfully")