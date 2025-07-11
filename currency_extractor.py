"""
Currency extraction and tracking module

Handles extraction of USD and Cambodian Riel amounts from text messages
and maintains running totals using database storage.
"""

import re
import logging
from datetime import datetime
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
    try:
        usd_amount = 0.0
        riel_amount = 0.0
        
        # Try specific ABA transaction patterns first (highest priority)
        # ABA USD format: "$272.50 paid by"
        aba_usd_match = re.search(r'"?\$([0-9,]+(?:\.\d{1,2})?)\s+paid\s+by', text, re.IGNORECASE)
        if aba_usd_match:
            usd_amount = float(aba_usd_match.group(1).replace(',', ''))
            logger.info(f"Detected ABA USD transaction: ${usd_amount:.2f}")
            return usd_amount, 0.0
        
        # ABA KHR format: "៛370,300 paid by"
        aba_khr_match = re.search(r'"?៛([0-9,]+(?:\.\d{1,2})?)\s+paid\s+by', text, re.IGNORECASE)
        if aba_khr_match:
            riel_amount = float(aba_khr_match.group(1).replace(',', ''))
            logger.info(f"Detected ABA KHR transaction: ៛{riel_amount:,.2f}")
            return 0.0, riel_amount
        
        # ABA KHR received format: "Received 110,000 KHR"
        aba_received_match = re.search(r'Received\s+([0-9,]+(?:\.\d{1,2})?)\s+KHR', text, re.IGNORECASE)
        if aba_received_match:
            riel_amount = float(aba_received_match.group(1).replace(',', ''))
            logger.info(f"Detected ABA received KHR: ៛{riel_amount:,.2f}")
            return 0.0, riel_amount
        
        # Standard USD patterns (fallback)
        usd_patterns = [
            r'\$([0-9,]+(?:\.\d{1,2})?)',  # $100, $100.50, $1,000.50
            r'([0-9,]+(?:\.\d{1,2})?)\$',  # 100$, 100.50$, 1,000.50$
            r'([0-9,]+(?:\.\d{1,2})?)\s*(?:USD|usd|dollars?|Dollars?)',  # 100 USD, 100 dollars
            r'USD?\s*([0-9,]+(?:\.\d{1,2})?)',  # USD 100, USD100
        ]
        
        for pattern in usd_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = float(match.replace(',', ''))
                usd_amount += amount
                logger.debug(f"Found USD amount: {amount} from pattern {pattern}")
        
        # Standard Cambodian Riel patterns (fallback)
        riel_patterns = [
            r'៛([0-9,]+(?:\.\d{1,2})?)',  # ៛25000, ៛25,000.50
            r'([0-9,]+(?:\.\d{1,2})?)៛',  # 25000៛, 25,000.50៛
            r'([0-9,]+(?:\.\d{1,2})?)\s*(?:KHR|khr|riel|Riel|riels|Riels)',  # 25000 KHR, 25000 riel
            r'(?:KHR|khr|riel|Riel)\s*([0-9,]+(?:\.\d{1,2})?)',  # KHR 25000, riel 25000
        ]
        
        for pattern in riel_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = float(match.replace(',', ''))
                riel_amount += amount
                logger.debug(f"Found KHR amount: {amount} from pattern {pattern}")
        
        if usd_amount > 0 or riel_amount > 0:
            logger.info(f"Extracted amounts from '{text}' - USD: ${usd_amount:.2f}, KHR: ៛{riel_amount:,.2f}")
        
        return usd_amount, riel_amount
        
    except Exception as e:
        logger.error(f"Error extracting amounts from text '{text}': {e}")
        return 0.0, 0.0

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
        payment_id = db.add_payment(user_id, username, chat_id, chat_title, 
                                   message_text, usd_amount, riel_amount)
        
        if usd_amount > 0 or riel_amount > 0:
            logger.info(f"Added payment {payment_id} - USD: ${usd_amount:.2f}, KHR: ៛{riel_amount:.2f}")
        
        return payment_id
    except Exception as e:
        logger.error(f"Error adding payment: {e}")
        return 0

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
        logger.error(f"Error getting totals: {e}")
        return 0.0, 0.0

def reset_totals() -> None:
    """
    Reset function kept for scheduler compatibility (no longer needed with database).
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] Daily reset check completed - using database storage")

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
        period_text = period.title()
        
        return f"📊 **{period_text}'s Totals:**\n💵 USD: ${usd_total:.2f}\n🏛️ KHR: ៛{riel_total:,.2f}"
    except Exception as e:
        logger.error(f"Error formatting totals: {e}")
        return f"❌ Error retrieving {period} totals"

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
        filename = db.export_to_excel(chat_id, chat_title, period)
        return filename
    except Exception as e:
        logger.error(f"Error exporting payments: {e}")
        return None
