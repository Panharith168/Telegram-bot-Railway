"""
Database operations for payment tracking

Handles all PostgreSQL database operations including payments storage,
retrieval, and Excel export functionality.
"""

import os
import logging
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import pytz

logger = logging.getLogger(__name__)

# Cambodia timezone
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_cambodia_datetime():
    """Get current datetime in Cambodia timezone."""
    return datetime.now(CAMBODIA_TZ)

def get_cambodia_date():
    """Get current date in Cambodia timezone."""
    return get_cambodia_datetime().date()

class PaymentDatabase:
    def __init__(self):
        self.connection = None
        self.connection_pool = None
    
    async def initialize(self):
        """Initialize database connection and setup tables."""
        await self.connect()
        await self.setup_tables()
    
    async def connect(self):
        """Establish database connection with retry logic."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL not found")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Database connection attempt {attempt + 1}/{max_retries}")
                
                # Try direct URL connection first
                self.connection = psycopg2.connect(
                    database_url,
                    sslmode='require',
                    cursor_factory=RealDictCursor
                )
                self.connection.autocommit = True
                
                # Test connection
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                
                logger.info("Database connection successful")
                return
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2)
    
    async def setup_tables(self):
        """Create necessary database tables."""
        try:
            with self.connection.cursor() as cursor:
                # Create payments table
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
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_chat_date 
                    ON payments(chat_id, payment_date)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_user 
                    ON payments(user_id)
                """)
                
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to setup tables: {e}")
            raise
    
    async def add_payment(self, user_id: int, username: str, chat_id: int, 
                         chat_title: str, message_text: str, 
                         usd_amount: float, riel_amount: float) -> int:
        """Add a new payment record."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO payments 
                    (user_id, username, chat_id, chat_title, message_text, 
                     usd_amount, riel_amount, payment_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id, username, chat_id, chat_title, message_text,
                    usd_amount, riel_amount, get_cambodia_date()
                ))
                
                payment_id = cursor.fetchone()['id']
                logger.info(f"Payment added: ID {payment_id}, ${usd_amount:.2f} USD, ៛{riel_amount:,.0f} KHR")
                return payment_id
                
        except Exception as e:
            logger.error(f"Failed to add payment: {e}")
            raise
    
    async def get_totals(self, chat_id: int, period: str = 'today') -> Tuple[float, float]:
        """Get payment totals for specified period."""
        try:
            with self.connection.cursor() as cursor:
                cambodia_date = get_cambodia_date()
                
                if period == 'today':
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0) as usd_total,
                               COALESCE(SUM(riel_amount), 0) as riel_total
                        FROM payments 
                        WHERE chat_id = %s AND payment_date = %s
                    """, (chat_id, cambodia_date))
                
                elif period == 'week':
                    week_start = cambodia_date - timedelta(days=7)
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0) as usd_total,
                               COALESCE(SUM(riel_amount), 0) as riel_total
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """, (chat_id, week_start))
                
                elif period == 'month':
                    month_start = cambodia_date.replace(day=1)
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0) as usd_total,
                               COALESCE(SUM(riel_amount), 0) as riel_total
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """, (chat_id, month_start))
                
                elif period == 'year':
                    year_start = cambodia_date.replace(month=1, day=1)
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0) as usd_total,
                               COALESCE(SUM(riel_amount), 0) as riel_total
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """, (chat_id, year_start))
                
                else:
                    # All time
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0) as usd_total,
                               COALESCE(SUM(riel_amount), 0) as riel_total
                        FROM payments 
                        WHERE chat_id = %s
                    """, (chat_id,))
                
                result = cursor.fetchone()
                return float(result['usd_total']), float(result['riel_total'])
                
        except Exception as e:
            logger.error(f"Failed to get totals: {e}")
            return 0.0, 0.0
    
    async def get_daily_summary(self, chat_id: int, target_date: date = None) -> Dict:
        """Get detailed daily summary."""
        if target_date is None:
            target_date = get_cambodia_date()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as payment_count,
                        COALESCE(SUM(usd_amount), 0) as usd_total,
                        COALESCE(SUM(riel_amount), 0) as riel_total,
                        ARRAY_AGG(
                            json_build_object(
                                'time', created_at,
                                'user', username,
                                'usd', usd_amount,
                                'riel', riel_amount,
                                'text', message_text
                            )
                        ) as payments
                    FROM payments 
                    WHERE chat_id = %s AND payment_date = %s
                    ORDER BY created_at DESC
                """, (chat_id, target_date))
                
                result = cursor.fetchone()
                return {
                    'date': target_date,
                    'payment_count': result['payment_count'],
                    'usd_total': float(result['usd_total']),
                    'riel_total': float(result['riel_total']),
                    'payments': result['payments'] or []
                }
                
        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}")
            return {
                'date': target_date,
                'payment_count': 0,
                'usd_total': 0.0,
                'riel_total': 0.0,
                'payments': []
            }
    
    async def export_payments(self, chat_id: int, period: str = 'month') -> Optional[str]:
        """Export payments to Excel file."""
        try:
            import pandas as pd
            from datetime import datetime
            
            # Calculate date range
            cambodia_date = get_cambodia_date()
            
            if period == 'week':
                start_date = cambodia_date - timedelta(days=7)
                filename = f"payments_week_{cambodia_date.strftime('%Y%m%d')}.xlsx"
            elif period == 'month':
                start_date = cambodia_date.replace(day=1)
                filename = f"payments_month_{cambodia_date.strftime('%Y%m')}.xlsx"
            elif period == 'year':
                start_date = cambodia_date.replace(month=1, day=1)
                filename = f"payments_year_{cambodia_date.year}.xlsx"
            else:  # all
                start_date = date(2020, 1, 1)  # Far past date
                filename = f"payments_all_{cambodia_date.strftime('%Y%m%d')}.xlsx"
            
            # Get payments data
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        payment_date,
                        created_at,
                        username,
                        usd_amount,
                        riel_amount,
                        message_text
                    FROM payments 
                    WHERE chat_id = %s AND payment_date >= %s
                    ORDER BY payment_date DESC, created_at DESC
                """, (chat_id, start_date))
                
                payments = cursor.fetchall()
            
            if not payments:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(payments)
            
            # Format columns
            df['usd_amount'] = df['usd_amount'].apply(lambda x: f"${float(x):.2f}")
            df['riel_amount'] = df['riel_amount'].apply(lambda x: f"៛{float(x):,.0f}")
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Rename columns
            df.columns = ['Date', 'Time', 'User', 'USD Amount', 'KHR Amount', 'Message']
            
            # Save to Excel
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Excel export created: {filename}")
            return filename
            
        except ImportError:
            logger.warning("pandas/openpyxl not available for Excel export")
            return None
        except Exception as e:
            logger.error(f"Failed to export payments: {e}")
            return None
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")