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
                        user_id BIGINT,
                        chat_id BIGINT,
                        usd_amount DECIMAL(10,2) DEFAULT 0,
                        riel_amount DECIMAL(15,2) DEFAULT 0,
                        payment_date DATE,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
            logger.info("Table ready")
        except Exception as e:
            logger.error(f"Table setup failed: {e}")
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