"""
Currency extraction and tracking module

Handles extraction of USD and Cambodian Riel amounts from text messages
and maintains running totals using database storage.
"""

import re
import logging
from typing import Tuple
from database import get_database

logger = logging.getLogger(__name__)

def extract_amounts(text: str) -> Tuple[float, float]:
    """
    Extract USD and Cambodian Riel amounts from text message.
    
    Supports multiple formats:
    - USD: $100, $100.50, 100$, 100.50$, $100.50 USD, 100 USD, 100 dollars
    - KHR: ៛25000, 25000៛, ៛25,000, 25000 riel, 25000 KHR
    
    Args:
        text (str): The message text to parse
        
    Returns:
        Tuple[float, float]: (usd_amount, riel_amount)
    """
    usd_amount = 0.0
    riel_amount = 0.0
    
    # Clean the text
    text = text.strip()
    
    try:
        # USD patterns - Enhanced for ABA transactions
        usd_patterns = [
            # Standard formats
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $100, $1,000.50
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\$',  # 100$, 1000.50$
            r'\$(\d+(?:\.\d{2})?)',  # $100.50, $100
            r'(\d+(?:\.\d{2})?)\$',  # 100.50$, 100$
            
            # ABA transaction formats
            r'\$(\d+(?:\.\d{2})?)\s+paid\s+by',  # $272.50 paid by
            r'paid\s+\$(\d+(?:\.\d{2})?)',  # paid $272.50
            r'Received\s+\$(\d+(?:\.\d{2})?)',  # Received $100
            r'Transfer\s+\$(\d+(?:\.\d{2})?)',  # Transfer $50
            
            # Word-based patterns
            r'(\d+(?:\.\d{2})?)\s+USD',  # 100.50 USD
            r'(\d+(?:\.\d{2})?)\s+dollars?',  # 100 dollars
            r'USD\s+(\d+(?:\.\d{2})?)',  # USD 100.50
            r'dollars?\s+(\d+(?:\.\d{2})?)',  # dollars 100
        ]
        
        for pattern in usd_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    amount = float(match.replace(',', ''))
                    if amount > usd_amount:  # Take the largest amount found
                        usd_amount = amount
                        logger.info(f"Detected ABA USD transaction: ${amount}")
                except ValueError:
                    continue
        
        # Cambodian Riel patterns
        riel_patterns = [
            r'៛(\d{1,3}(?:,\d{3})*)',  # ៛25,000
            r'(\d{1,3}(?:,\d{3})*)៛',  # 25,000៛
            r'៛(\d+)',  # ៛25000
            r'(\d+)៛',  # 25000៛
            r'(\d{1,3}(?:,\d{3})*)\s+riel',  # 25,000 riel
            r'(\d{1,3}(?:,\d{3})*)\s+KHR',  # 25,000 KHR
            r'riel\s+(\d{1,3}(?:,\d{3})*)',  # riel 25,000
            r'KHR\s+(\d{1,3}(?:,\d{3})*)',  # KHR 25,000
            r'Received\s+(\d{1,3}(?:,\d{3})*)\s+KHR',  # Received 110,000 KHR
        ]
        
        for pattern in riel_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    amount = float(match.replace(',', ''))
                    if amount > riel_amount:  # Take the largest amount found
                        riel_amount = amount
                        logger.info(f"Detected Riel amount: ៛{amount}")
                except ValueError:
                    continue
        
        # Log the extraction result
        if usd_amount > 0 or riel_amount > 0:
            logger.info(f"Extracted from '{text}': ${usd_amount} USD, ៛{riel_amount} KHR")
        
    except Exception as e:
        logger.error(f"Error extracting amounts from '{text}': {e}")
    
    return usd_amount, riel_amount

def add_payment(user_id: int, username: str, chat_id: int, chat_title: str, 
               message_text: str, usd_amount: float, riel_amount: float) -> int:
    """
    Add a payment to the database.
    
    Args:
        user_id (int): Telegram user ID
        username (str): Telegram username
        chat_id (int): Telegram chat ID
        chat_title (str): Chat title
        message_text (str): Original message text
        usd_amount (float): USD amount to add
        riel_amount (float): Riel amount to add
        
    Returns:
        int: Payment ID
    """
    try:
        db = get_database()
        payment_id = db.add_payment(
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            chat_title=chat_title,
            message_text=message_text,
            usd_amount=usd_amount,
            riel_amount=riel_amount
        )
        logger.info(f"Payment added successfully: ID {payment_id}")
        return payment_id
    except Exception as e:
        logger.error(f"Failed to add payment: {e}")
        raise

def get_totals(chat_id: int, period: str = 'today') -> Tuple[float, float]:
    """
    Get totals for specified period.
    
    Args:
        chat_id (int): Chat ID to get totals for
        period (str): 'today', 'week', 'month', or 'year'
    
    Returns:
        Tuple[float, float]: (usd_total, riel_total)
    """
    try:
        db = get_database()
        return db.get_totals(chat_id, period)
    except Exception as e:
        logger.error(f"Failed to get totals: {e}")
        return 0.0, 0.0

def reset_totals() -> None:
    """
    Reset function kept for scheduler compatibility (no longer needed with database).
    """
    logger.info("Reset function called (no action needed with database storage)")

def format_totals(chat_id: int, period: str = 'today') -> str:
    """
    Format current totals for display.
    
    Args:
        chat_id (int): Chat ID to get totals for
        period (str): Period to display
    
    Returns:
        str: Formatted totals string
    """
    try:
        usd_total, riel_total = get_totals(chat_id, period)
        
        period_names = {
            'today': "Today's",
            'week': "This Week's",
            'month': "This Month's", 
            'year': "This Year's"
        }
        
        period_display = period_names.get(period, period.title())
        
        formatted = f"📊 **{period_display} Totals:**\n"
        formatted += f"💵 USD: ${usd_total:.2f}\n"
        formatted += f"🏛️ KHR: ៛{riel_total:,.2f}"
        
        return formatted
    except Exception as e:
        logger.error(f"Error formatting totals: {e}")
        return "❌ Error retrieving totals"

def export_payments(chat_id: int, chat_title: str, period: str = 'month') -> str:
    """
    Export payments to Excel file.
    
    Args:
        chat_id (int): Chat ID to export
        chat_title (str): Chat title for filename
        period (str): Period to export ('week', 'month', 'year', 'all')
    
    Returns:
        str: Filename of exported file or None if failed
    """
    try:
        db = get_database()
        return db.export_to_excel(chat_id, chat_title, period)
    except Exception as e:
        logger.error(f"Failed to export payments: {e}")
        return None