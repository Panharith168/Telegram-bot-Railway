"""
Ultra Simple Database - Railway Compatible

Minimal database operations to avoid Railway connection issues.
"""

import os
import logging
import psycopg2
from urllib.parse import urlparse
from datetime import datetime, date
from typing import Tuple
import pytz

logger = logging.getLogger(__name__)

# Cambodia timezone
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_cambodia_date():
    return datetime.now(CAMBODIA_TZ).date()

class PaymentDatabase:
    def __init__(self):
        self.connection = None
        self.connect()
        self.setup_database()
    
    def add_payment(self, user_id: int, username: str, chat_id: int, chat_title: str, 
                   message_text: str, usd_amount: float, riel_amount: float) -> int:
        """Add a new payment record."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO payments 
                    (user_id, username, chat_id, chat_title, message_text, 
                     usd_amount, riel_amount, payment_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, username, chat_id, chat_title, message_text, 
                      usd_amount, riel_amount, get_cambodia_date()))
                
                payment_id = cursor.fetchone()[0]
                logger.info(f"Payment added: ID {payment_id}, ${usd_amount:.2f} USD, ៛{riel_amount:.2f} KHR")
                return payment_id
        except Exception as e:
            logger.error(f"Failed to add payment: {e}")
            raise
    
    def get_totals(self, chat_id: int, period: str = 'today') -> tuple:
        """Get totals for specified period."""
        try:
            with self.connection.cursor() as cursor:
                cambodia_date = get_cambodia_date()
                
                if period == 'today':
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date = %s
                    """, (chat_id, cambodia_date))
                elif period == 'week':
                    import datetime
                    week_start = cambodia_date - datetime.timedelta(days=7)
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """, (chat_id, week_start))
                elif period == 'month':
                    month_start = cambodia_date.replace(day=1)
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """, (chat_id, month_start))
                elif period == 'year':
                    year_start = cambodia_date.replace(month=1, day=1)
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """, (chat_id, year_start))
                
                result = cursor.fetchone()
                return float(result[0]), float(result[1])
        except Exception as e:
            logger.error(f"Failed to get totals: {e}")
            return 0.0, 0.0
    
    def export_to_excel(self, chat_id: int, chat_title: str, period: str = 'month') -> str:
        """Export payments to Excel - simplified for Railway."""
        # For Railway deployment, we'll skip Excel export to avoid dependency issues
        logger.info("Excel export not available in Railway deployment")
        return None
    
    def connect(self):
        """Simple Railway connection."""
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise Exception("No DATABASE_URL found")
        
        logger.info("Connecting to Railway database...")
        
        try:
            # Parse URL
            parsed = urlparse(database_url)
            
            # Simple connection with SSL
            self.connection = psycopg2.connect(
                host=parsed.hostname,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password,
                port=parsed.port or 5432,
                sslmode='require'
            )
            self.connection.autocommit = True
            logger.info("Railway connection successful")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def setup_database(self):
        """Create table."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        username VARCHAR(100),
                        chat_id BIGINT NOT NULL,
                        chat_title VARCHAR(200),
                        message_text TEXT NOT NULL,
                        usd_amount DECIMAL(10,2) DEFAULT 0,
                        riel_amount DECIMAL(15,2) DEFAULT 0,
                        payment_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_chat_date 
                    ON payments(chat_id, payment_date)
                """)
                
            logger.info("Database tables ready")
        except Exception as e:
            logger.error(f"Table setup failed: {e}")
            raise
            raise
    
    def add_payment(self, user_id: int, username: str, chat_id: int, chat_title: str, 
                   message_text: str, usd_amount: float, riel_amount: float) -> int:
        """Add payment."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO payments (user_id, chat_id, usd_amount, riel_amount, payment_date)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (user_id, chat_id, usd_amount, riel_amount, get_cambodia_date()))
                
                payment_id = cursor.fetchone()[0]
                logger.info(f"Payment added: ${usd_amount} USD, ៛{riel_amount} KHR")
                return payment_id
        except Exception as e:
            logger.error(f"Add payment failed: {e}")
            raise
    
    def get_totals(self, chat_id: int, period: str = 'today') -> Tuple[float, float]:
        """Get totals."""
        try:
            with self.connection.cursor() as cursor:
                today = get_cambodia_date()
                
                cursor.execute("""
                    SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                    FROM payments 
                    WHERE chat_id = %s AND payment_date = %s
                """, (chat_id, today))
                
                result = cursor.fetchone()
                usd_total, riel_total = float(result[0]), float(result[1])
                logger.info(f"Totals: ${usd_total} USD, ៛{riel_total} KHR")
                return usd_total, riel_total
                
        except Exception as e:
            logger.error(f"Get totals failed: {e}")
            return 0.0, 0.0

def get_database():
    """Get database instance."""
    return PaymentDatabase()