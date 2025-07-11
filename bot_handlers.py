"""
Telegram bot message and command handlers

Contains all the handlers for processing messages and commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler
from telegram.constants import ParseMode

from currency_extractor import extract_amounts, add_payment, format_totals, export_payments

logger = logging.getLogger(__name__)

async def add_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /add command to manually add payment amounts.
    Usage: /add $100 or /add ៛25000 or /add $50 ៛10000
    """
    try:
        # Get user and chat information
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        chat_id = update.effective_chat.id
        chat_title = getattr(update.effective_chat, 'title', 'Private Chat')
        
        # Check if arguments are provided
        if not context.args:
            help_message = (
                "💰 **Add Payment Command**\n\n"
                "**Usage:**\n"
                "• `/add $100` - Add USD payment\n"
                "• `/add ៛25000` - Add KHR payment\n"
                "• `/add $50 ៛10000` - Add both currencies\n"
                "• `/add I paid $272.50 for lunch` - Parse from text\n\n"
                "**Examples:**\n"
                "• `/add $272.50`\n"
                "• `/add ៛100,000`\n"
                "• `/add Received $50 payment`"
            )
            await update.message.reply_text(help_message, parse_mode='Markdown')
            return
        
        # Join all arguments into a single text
        text = " ".join(context.args)
        
        logger.info(f"Manual payment addition by user {user_id} in chat {chat_id}: {text}")
        
        # Extract currency amounts
        usd_amount, riel_amount = extract_amounts(text)
        
        # Check if any amount was detected
        if usd_amount == 0 and riel_amount == 0:
            error_message = (
                "❌ No payment amounts detected in your text.\n\n"
                "Try: `/add $100` or `/add ៛25000`"
            )
            await update.message.reply_text(error_message)
            return
        
        # Add payment to database
        payment_id = add_payment(
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            chat_title=chat_title,
            message_text=f"Manual entry: {text}",
            usd_amount=usd_amount,
            riel_amount=riel_amount
        )
        
        # Get updated totals for today
        from currency_extractor import get_totals
        current_usd, current_riel = get_totals(chat_id, 'today')
        
        # Create response message
        response_parts = ["✅ **Payment Added:**"]
        
        if usd_amount > 0:
            response_parts.append(f"💵 ${usd_amount:.2f} USD")
        if riel_amount > 0:
            response_parts.append(f"🏛️ ៛{riel_amount:,.2f} KHR")
        
        response_parts.append(f"\n📊 **Today's Total:**")
        response_parts.append(f"💵 ${current_usd:.2f} USD")
        response_parts.append(f"🏛️ ៛{current_riel:,.2f} KHR")
        
        response_message = "\n".join(response_parts)
        await update.message.reply_text(response_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in add_payment_command: {e}")
        await update.message.reply_text("❌ Error adding payment. Please try again.")

async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /total command to display current totals.
    """
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        logger.info(f"Total command requested by user {user_id} in chat {chat_id} (type: {chat_type})")
        
        # Get today's totals
        totals_text = format_totals(chat_id, 'today')
        
        await update.message.reply_text(totals_text, parse_mode='Markdown')
        logger.info(f"Successfully sent totals response to chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in show_total: {e}")
        await update.message.reply_text("❌ Error retrieving totals. Please try again.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command with welcome message.
    """
    try:
        welcome_message = (
            "🤖 **Biomed Payment Bot**\n\n"
            "I help track your payment amounts with support for:\n"
            "💵 USD ($100, $50.25)\n"
            "🏛️ Cambodian Riel (៛25000, ៛100,000)\n\n"
            "✨ **Features:**\n"
            "📊 Daily/weekly/monthly totals\n"
            "🔄 Automatic currency detection\n"
            "📈 Historical tracking\n"
            "📋 Excel export functionality\n\n"
        )
        
        welcome_message += (
            "**How to use:**\n"
            "1. Use `/add $100` to manually add payments\n"
            "2. Use `/total` to check your totals\n"
            "3. Use `/test` to test payment detection\n\n"
            "**Example:**\n"
            "`/add $272.50 paid for lunch`"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ Error showing welcome message.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.
    """
    try:
        help_text = (
            "🤖 **Payment Bot Commands**\n\n"
            "**Basic Commands:**\n"
            "• `/start` - Welcome message\n"
            "• `/add $100` - Add payment manually\n"
            "• `/total` - Show today's totals\n"
            "• `/help` - Show this help\n\n"
            "**Time Period Commands:**\n"
            "• `/week` - This week's totals\n"
            "• `/month` - This month's totals\n"
            "• `/year` - This year's totals\n"
            "• `/summary` - Detailed daily summary\n\n"
            "**Export & Testing:**\n"
            "• `/export` - Export to Excel\n"
            "• `/test [text]` - Test payment detection\n\n"
            "**Supported Formats:**\n"
            "💵 USD: $100, $50.25, 100$\n"
            "🏛️ KHR: ៛25000, ៛100,000, 25000៛\n"
            "📱 ABA: \"$272.50 paid by...\""
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("❌ Error showing help.")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /summary command to show detailed daily summary.
    """
    try:
        chat_id = update.effective_chat.id
        
        # Get today's totals
        from currency_extractor import get_totals
        current_usd, current_riel = get_totals(chat_id, 'today')
        
        # Get current date
        from database import get_cambodia_date
        today = get_cambodia_date()
        
        summary_text = f"📊 **Daily Payment Summary**\n"
        summary_text += f"📅 Date: {today.strftime('%B %d, %Y')}\n\n"
        summary_text += f"💰 **Total Payments:**\n"
        summary_text += f"💵 USD: ${current_usd:.2f}\n"
        summary_text += f"🏛️ KHR: ៛{current_riel:,.2f}\n\n"
        
        if current_usd == 0 and current_riel == 0:
            summary_text += "No payments added today.\nUse `/add $100` to add payments manually."
        else:
            summary_text += "✅ All payments added via `/add` command!"
        
        await update.message.reply_text(summary_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in summary command: {e}")
        await update.message.reply_text("❌ Error generating summary.")

async def weekly_totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /week command to display weekly totals."""
    try:
        chat_id = update.effective_chat.id
        totals_text = format_totals(chat_id, 'week')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in weekly_totals: {e}")
        await update.message.reply_text("❌ Error retrieving weekly totals.")

async def monthly_totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /month command to display monthly totals."""
    try:
        chat_id = update.effective_chat.id
        totals_text = format_totals(chat_id, 'month')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in monthly_totals: {e}")
        await update.message.reply_text("❌ Error retrieving monthly totals.")

async def yearly_totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /year command to display yearly totals."""
    try:
        chat_id = update.effective_chat.id
        totals_text = format_totals(chat_id, 'year')
        await update.message.reply_text(totals_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in yearly_totals: {e}")
        await update.message.reply_text("❌ Error retrieving yearly totals.")

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command to export payments to Excel."""
    try:
        chat_id = update.effective_chat.id
        chat_title = getattr(update.effective_chat, 'title', 'Private_Chat')
        
        # Determine period from command arguments
        period = 'month'  # default
        if context.args:
            arg = context.args[0].lower()
            if arg in ['week', 'month', 'year', 'all']:
                period = arg
        
        # Generate Excel file
        filename = export_payments(chat_id, chat_title, period)
        
        if filename:
            # Send the file
            with open(filename, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=f"📊 Payment export for {period}"
                )
            
            # Clean up the file
            import os
            os.remove(filename)
        else:
            await update.message.reply_text("❌ No payments found for export.")
            
    except Exception as e:
        logger.error(f"Error in export_excel: {e}")
        await update.message.reply_text("❌ Error exporting payments.")

async def test_detection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /test command to test payment detection manually."""
    try:
        if not context.args:
            test_message = (
                "🧪 **Test Payment Detection**\n\n"
                "Usage: `/test [your text]`\n\n"
                "Example: `/test I paid $50 for lunch`\n"
                "This will show what amounts would be detected without saving them."
            )
            await update.message.reply_text(test_message, parse_mode='Markdown')
            return
        
        # Join arguments to form test text
        test_text = " ".join(context.args)
        
        # Extract amounts without saving
        usd_amount, riel_amount = extract_amounts(test_text)
        
        # Format response
        response = f"🧪 **Detection Test Results:**\n\n"
        response += f"📝 **Input:** {test_text}\n\n"
        response += f"💰 **Detected Amounts:**\n"
        
        if usd_amount > 0:
            response += f"💵 USD: ${usd_amount:.2f}\n"
        if riel_amount > 0:
            response += f"🏛️ KHR: ៛{riel_amount:,.2f}\n"
        
        if usd_amount == 0 and riel_amount == 0:
            response += "❌ No amounts detected\n"
        else:
            response += f"\n✅ Detection successful!"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in test_detection: {e}")
        await update.message.reply_text("❌ Error testing detection.")

def setup_handlers(app: Application) -> None:
    """
    Setup all command handlers for the bot.
    """
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_payment_command))
    app.add_handler(CommandHandler("total", show_total))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("week", weekly_totals))
    app.add_handler(CommandHandler("month", monthly_totals))
    app.add_handler(CommandHandler("year", yearly_totals))
    app.add_handler(CommandHandler("export", export_excel))
    app.add_handler(CommandHandler("test", test_detection))
    
    # No automatic message handler - only respond to commands
    logger.info("All command handlers registered successfully")