"""
Database operations for payment tracking - SIMPLE RAILWAY VERSION

Handles all database operations with simplified Railway connection.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
import pandas as pd
import pytz

logger = logging.getLogger(__name__)

# Cambodia timezone (UTC+7)
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_cambodia_date():
    """Get current date in Cambodia timezone."""
    return datetime.now(CAMBODIA_TZ).date()

def get_cambodia_datetime():
    """Get current datetime in Cambodia timezone."""
    return datetime.now(CAMBODIA_TZ)

class PaymentDatabase:
    def __init__(self):
        self.connection = None
        self.connect()
        self.setup_database()
    
    def connect(self):
        """Connect to PostgreSQL database - Railway optimized."""
        try:
            # Method 1: Direct environment variables (most reliable for Railway)
            host = os.getenv('PGHOST')
            database = os.getenv('PGDATABASE') 
            user = os.getenv('PGUSER')
            password = os.getenv('PGPASSWORD')
            port = os.getenv('PGPORT', '5432')
            
            if all([host, database, user, password]):
                logger.info(f"Connecting with individual variables: {host}:{port}")
                self.connection = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=int(port),
                    sslmode='require'  # Railway requires SSL
                )
                self.connection.autocommit = True
                logger.info("Successfully connected via individual environment variables")
                return
            
            # Method 2: DATABASE_URL with SSL requirement
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                # Ensure SSL mode for Railway
                if '?sslmode=' not in database_url:
                    database_url += '?sslmode=require'
                
                logger.info("Attempting DATABASE_URL connection with SSL")
                self.connection = psycopg2.connect(database_url)
                self.connection.autocommit = True
                logger.info("Successfully connected via DATABASE_URL")
                return
            
            raise Exception("No valid database credentials found")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            # Log available environment for debugging
            logger.error(f"PGHOST: {bool(os.getenv('PGHOST'))}")
            logger.error(f"PGDATABASE: {bool(os.getenv('PGDATABASE'))}")
            logger.error(f"PGUSER: {bool(os.getenv('PGUSER'))}")
            logger.error(f"PGPASSWORD: {bool(os.getenv('PGPASSWORD'))}")
            logger.error(f"DATABASE_URL: {bool(os.getenv('DATABASE_URL'))}")
            raise
    
    def setup_database(self):
        """Create tables if they don't exist."""
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
                
                logger.info("Database tables verified/created successfully")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
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
    
    def get_totals(self, chat_id: int, period: str = 'today') -> Tuple[float, float]:
        """Get totals for specified period."""
        try:
            with self.connection.cursor() as cursor:
                cambodia_date = get_cambodia_date()
                
                if period == 'today':
                    query = """
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date = %s
                    """
                    cursor.execute(query, (chat_id, cambodia_date))
                    
                elif period == 'week':
                    week_start = cambodia_date - pd.Timedelta(days=7)
                    query = """
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """
                    cursor.execute(query, (chat_id, week_start))
                    
                elif period == 'month':
                    month_start = cambodia_date.replace(day=1)
                    query = """
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """
                    cursor.execute(query, (chat_id, month_start))
                    
                elif period == 'year':
                    year_start = cambodia_date.replace(month=1, day=1)
                    query = """
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= %s
                    """
                    cursor.execute(query, (chat_id, year_start))
                
                result = cursor.fetchone()
                usd_total, riel_total = float(result[0]), float(result[1])
                logger.info(f"Totals for chat {chat_id} ({period}): ${usd_total:.2f} USD, ៛{riel_total:.2f} KHR")
                return usd_total, riel_total
                
        except Exception as e:
            logger.error(f"Failed to get totals for chat {chat_id}, period {period}: {e}")
            return 0.0, 0.0
    
    def get_payments_for_export(self, chat_id: int, start_date: date = None, 
                               end_date: date = None) -> List[Dict]:
        """Get payment records for export."""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                if start_date and end_date:
                    cursor.execute("""
                        SELECT payment_date, username, message_text, 
                               usd_amount, riel_amount, created_at
                        FROM payments 
                        WHERE chat_id = %s AND payment_date BETWEEN %s AND %s
                        ORDER BY payment_date DESC, created_at DESC
                    """, (chat_id, start_date, end_date))
                else:
                    cursor.execute("""
                        SELECT payment_date, username, message_text, 
                               usd_amount, riel_amount, created_at
                        FROM payments 
                        WHERE chat_id = %s
                        ORDER BY payment_date DESC, created_at DESC
                    """, (chat_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get payments for export: {e}")
            return []
    
    def export_to_excel(self, chat_id: int, chat_title: str, period: str = 'all') -> str:
        """Export payments to Excel file."""
        try:
            start_date = None
            end_date = get_cambodia_date()
            
            if period == 'week':
                start_date = get_cambodia_date() - pd.Timedelta(days=7)
            elif period == 'month':
                start_date = get_cambodia_date().replace(day=1)
            elif period == 'year':
                start_date = get_cambodia_date().replace(month=1, day=1)
            
            payments = self.get_payments_for_export(chat_id, start_date, end_date)
            
            if not payments:
                return None
            
            df = pd.DataFrame(payments)
            df['usd_amount'] = df['usd_amount'].astype(float)
            df['riel_amount'] = df['riel_amount'].astype(float)
            
            timestamp = get_cambodia_datetime().strftime('%Y%m%d_%H%M%S')
            safe_title = "".join(c for c in chat_title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"payments_{safe_title}_{period}_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Payments', index=False)
                
                summary_data = {
                    'Period': [period.title()],
                    'Total USD': [df['usd_amount'].sum()],
                    'Total KHR': [df['riel_amount'].sum()],
                    'Number of Payments': [len(df)],
                    'Export Date': [get_cambodia_datetime().strftime('%Y-%m-%d %H:%M:%S')]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"Exported {len(payments)} payments to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return None
    
    def get_stats(self, chat_id: int) -> Dict:
        """Get comprehensive statistics."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                    FROM payments WHERE chat_id = %s
                """, (chat_id,))
                total_count, total_usd, total_riel = cursor.fetchone()
                
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                    FROM payments WHERE chat_id = %s AND payment_date = %s
                """, (chat_id, get_cambodia_date()))
                today_count, today_usd, today_riel = cursor.fetchone()
                
                return {
                    'total_payments': total_count,
                    'total_usd': float(total_usd),
                    'total_riel': float(total_riel),
                    'today_payments': today_count,
                    'today_usd': float(today_usd),
                    'today_riel': float(today_riel)
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

def get_database():
    """Get database instance."""
    return PaymentDatabase()