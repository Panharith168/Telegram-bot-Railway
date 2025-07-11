"""
Telegram bot message and command handlers

Contains all the handlers for processing messages and commands.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler, 
    ContextTypes, filters
)

from currency_extractor import extract_amounts, add_payment, format_totals, export_payments

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages and extract currency amounts.
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context
    """
    try:
        if not update.message or not update.message.text:
            return
            
        message_text = update.message.text
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        chat_id = update.effective_chat.id if update.effective_chat else "Unknown"
        
        logger.info(f"Processing message from user {user_id} in chat {chat_id}: {message_text}")
        
        # Extract amounts from the message
        usd_amount, riel_amount = extract_amounts(message_text)
        
        # Add payment to database if any amounts found
        if usd_amount > 0 or riel_amount > 0:
            username = update.effective_user.username or update.effective_user.first_name or "Unknown"
            chat_title = update.effective_chat.title or "Private Chat"
            
            payment_id = add_payment(
                user_id=user_id,
                username=username,
                chat_id=chat_id,
                chat_title=chat_title,
                message_text=message_text,
                usd_amount=usd_amount,
                riel_amount=riel_amount
            )
            
            # Send confirmation showing what was detected and current totals
            from currency_extractor import get_totals
            current_usd, current_riel = get_totals(chat_id, 'today')
            
            detected_msg = f"💰 Detected: "
            if usd_amount > 0:
                detected_msg += f"${usd_amount:.2f} USD"
            if riel_amount > 0:
                if usd_amount > 0:
                    detected_msg += f" + ៛{riel_amount:,.2f} KHR"
                else:
                    detected_msg += f"៛{riel_amount:,.2f} KHR"
            
            totals_msg = f"\n📊 Today's Total: ${current_usd:.2f} USD + ៛{current_riel:,.2f} KHR"
            
            await update.message.reply_text(detected_msg + totals_msg)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")

async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /total command to display current totals.
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context
    """
    try:
        if not update.message:
            return
            
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        chat_id = update.effective_chat.id if update.effective_chat else "Unknown"
        chat_type = update.effective_chat.type if update.effective_chat else "Unknown"
        logger.info(f"Total command requested by user {user_id} in chat {chat_id} (type: {chat_type})")
        
        totals_text = format_totals(chat_id, 'today')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
        logger.info(f"Successfully sent totals response to chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error showing totals: {e}")
        await update.message.reply_text("❌ Sorry, there was an error retrieving the totals.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command with welcome message.
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context
    """
    try:
        if not update.message:
            return
            
        # Check if this is a group chat to provide privacy setup guidance
        is_group = update.effective_chat.type in ['group', 'supergroup']
        
        welcome_message = (
            "🤖 **Payment Tracking Bot**\n\n"
            "I automatically track payment amounts with persistent database storage and comprehensive reporting!\n\n"
            "**Supported currencies:**\n"
            "💵 USD: $10.50\n"
            "🏛️ KHR: ៛25,000\n\n"
            "**Commands:**\n"
            "• /total - Show today's totals\n"
            "• /week - Show weekly totals\n"
            "• /month - Show monthly totals\n"
            "• /year - Show yearly totals\n"
            "• /summary - Detailed daily summary\n"
            "• /export [period] - Export to Excel (week/month/year/all)\n"
            "• /help - Show this help message\n\n"
            "**Features:**\n"
            "📊 Persistent database storage\n"
            "🔒 Multi-chat support\n"
            "📈 Historical tracking\n"
            "📋 Excel export functionality\n\n"
        )
        
        if is_group:
            welcome_message += (
                "⚠️ **IMPORTANT FOR GROUPS:**\n"
                "To track payments from regular messages, bot privacy must be disabled:\n\n"
                "1. Go to @BotFather on Telegram\n"
                "2. Send /mybots\n"
                "3. Select this bot\n"
                "4. Go to 'Bot Settings' → 'Group Privacy'\n"
                "5. Select 'Disable'\n\n"
                "Without this, I can only see commands (like /total) but not regular payment messages!"
            )
        else:
            welcome_message += "Just send messages with payment amounts and I'll track them automatically!"
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context
    """
    await start_command(update, context)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /summary command to show detailed daily summary.
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context
    """
    try:
        if not update.message:
            return
            
        from currency_extractor import get_totals
        from datetime import datetime
        
        chat_id = update.effective_chat.id
        current_usd, current_riel = get_totals(chat_id, 'today')
        today = datetime.now().strftime('%B %d, %Y')
        
        summary_text = f"📋 **Daily Payment Summary**\n"
        summary_text += f"📅 Date: {today}\n\n"
        summary_text += f"💰 **Total Payments:**\n"
        summary_text += f"💵 USD: ${current_usd:.2f}\n"
        summary_text += f"🏛️ KHR: ៛{current_riel:,.2f}\n\n"
        
        if current_usd == 0 and current_riel == 0:
            summary_text += "No payments detected today."
        else:
            summary_text += "✅ All payments automatically tracked from your messages!"
        
        await update.message.reply_text(summary_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing summary: {e}")
        await update.message.reply_text("❌ Sorry, there was an error generating the summary.")

async def weekly_totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /week command to display weekly totals."""
    try:
        if not update.message:
            return
        
        chat_id = update.effective_chat.id
        totals_text = format_totals(chat_id, 'week')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing weekly totals: {e}")
        await update.message.reply_text("❌ Sorry, there was an error retrieving weekly totals.")

async def monthly_totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /month command to display monthly totals."""
    try:
        if not update.message:
            return
        
        chat_id = update.effective_chat.id
        totals_text = format_totals(chat_id, 'month')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing monthly totals: {e}")
        await update.message.reply_text("❌ Sorry, there was an error retrieving monthly totals.")

async def yearly_totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /year command to display yearly totals."""
    try:
        if not update.message:
            return
        
        chat_id = update.effective_chat.id
        totals_text = format_totals(chat_id, 'year')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing yearly totals: {e}")
        await update.message.reply_text("❌ Sorry, there was an error retrieving yearly totals.")

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command to export payments to Excel."""
    try:
        if not update.message:
            return
        
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title or "Private Chat"
        
        # Default to monthly export, allow period specification
        period = 'month'
        if context.args:
            period_arg = context.args[0].lower()
            if period_arg in ['week', 'month', 'year', 'all']:
                period = period_arg
        
        await update.message.reply_text("🔄 Generating Excel export... Please wait.")
        
        filename = export_payments(chat_id, chat_title, period)
        
        if filename:
            # Send the file
            with open(filename, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=f"📊 Payment export for {period} period\n"
                           f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            # Clean up the file
            import os
            os.remove(filename)
        else:
            await update.message.reply_text("❌ Failed to generate export or no payments found for the specified period.")
        
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        await update.message.reply_text("❌ Sorry, there was an error generating the export.")

async def test_detection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /test command to test payment detection manually."""
    try:
        if not update.message:
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Test Payment Detection**\n\n"
                "Usage: `/test <message>`\n\n"
                "Examples:\n"
                "• `/test I paid $50.25 for lunch`\n"
                "• `/test Cost was ៛25,000 for taxi`\n"
                "• `/test Total: $100.00 and ៛5,000`"
            )
            return
        
        test_message = " ".join(context.args)
        from currency_extractor import extract_amounts
        
        usd_amount, riel_amount = extract_amounts(test_message)
        
        result_text = f"🔍 **Detection Test Results**\n\n"
        result_text += f"**Input:** {test_message}\n\n"
        result_text += f"**Detected:**\n"
        result_text += f"💵 USD: ${usd_amount:.2f}\n"
        result_text += f"🏛️ KHR: ៛{riel_amount:,.2f}\n\n"
        
        if usd_amount > 0 or riel_amount > 0:
            result_text += "✅ **Detection successful!** This message would be tracked."
        else:
            result_text += "❌ **No amounts detected.** This message would be ignored."
        
        await update.message.reply_text(result_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in test detection: {e}")
        await update.message.reply_text("❌ Sorry, there was an error testing the detection.")

def setup_handlers(app: Application) -> None:
    """
    Setup all message and command handlers for the bot.
    
    Args:
        app (Application): Telegram application instance
    """
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("total", show_total))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("week", weekly_totals))
    app.add_handler(CommandHandler("month", monthly_totals))
    app.add_handler(CommandHandler("year", yearly_totals))
    app.add_handler(CommandHandler("export", export_excel))
    app.add_handler(CommandHandler("test", test_detection))
    
    # Message handler for text messages (excluding commands)
    app.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND), 
        handle_message
    ))
    
    logger.info("All handlers registered successfully")
