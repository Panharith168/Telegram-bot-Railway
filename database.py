"""
Database operations for payment tracking - RAILWAY FIXED VERSION

Handles all database operations including payments, totals, and export functionality.
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
        """Connect to PostgreSQL database with improved Railway compatibility."""
        try:
            # Get DATABASE_URL
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL not found in environment")
                raise Exception("DATABASE_URL not found")
            
            logger.info(f"DATABASE_URL detected: {database_url[:30]}...")
            
            # Railway sometimes provides malformed DATABASE_URL, let's clean it
            if database_url.startswith('postgresql://'):
                # This is correct format
                self.connection = psycopg2.connect(database_url)
            elif database_url.startswith('postgres://'):
                # Convert postgres:// to postgresql://
                fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
                logger.info("Converting postgres:// to postgresql://")
                self.connection = psycopg2.connect(fixed_url)
            else:
                # Parse individual components from URL
                logger.info("Parsing DATABASE_URL components manually")
                # Extract components manually for Railway compatibility
                from urllib.parse import urlparse
                parsed = urlparse(database_url)
                
                self.connection = psycopg2.connect(
                    host=parsed.hostname,
                    database=parsed.path.lstrip('/'),
                    user=parsed.username,
                    password=parsed.password,
                    port=parsed.port or 5432
                )
            
            self.connection.autocommit = True
            logger.info("Connected to PostgreSQL database successfully")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.error(f"DATABASE_URL format: {os.getenv('DATABASE_URL', 'NOT_SET')[:50]}...")
            
            # Try fallback connection with individual variables
            try:
                logger.info("Attempting fallback connection with individual variables")
                self.connection = psycopg2.connect(
                    host=os.getenv('PGHOST'),
                    database=os.getenv('PGDATABASE'),
                    user=os.getenv('PGUSER'),
                    password=os.getenv('PGPASSWORD'),
                    port=os.getenv('PGPORT', 5432)
                )
                self.connection.autocommit = True
                logger.info("Connected via fallback method")
            except Exception as fallback_error:
                logger.error(f"Fallback connection also failed: {fallback_error}")
                raise Exception(f"All database connection methods failed: {e}")
    
    def setup_database(self):
        """Create tables if they don't exist."""
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_date 
                    ON payments(payment_date)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_chat 
                    ON payments(chat_id, payment_date)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_user 
                    ON payments(user_id, payment_date)
                """)
                
                logger.info("Database tables created successfully")
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
                logger.info(f"Added payment {payment_id}: ${usd_amount:.2f} USD, ៛{riel_amount:.2f} KHR")
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
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date = %s
                    """, (chat_id, cambodia_date))
                elif period == 'week':
                    week_start = cambodia_date - pd.Timedelta(days=7)
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
                usd_total, riel_total = float(result[0]), float(result[1])
                logger.info(f"Retrieved totals for chat {chat_id} ({period}): ${usd_total:.2f} USD, ៛{riel_total:.2f} KHR")
                return usd_total, riel_total
                
        except Exception as e:
            logger.error(f"Failed to get totals for chat {chat_id}: {e}")
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
            # Determine date range based on period using Cambodia timezone
            start_date = None
            end_date = get_cambodia_date()
            
            if period == 'week':
                start_date = get_cambodia_date() - pd.Timedelta(days=7)
            elif period == 'month':
                start_date = get_cambodia_date().replace(day=1)
            elif period == 'year':
                start_date = get_cambodia_date().replace(month=1, day=1)
            
            # Get payment data
            payments = self.get_payments_for_export(chat_id, start_date, end_date)
            
            if not payments:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(payments)
            df['usd_amount'] = df['usd_amount'].astype(float)
            df['riel_amount'] = df['riel_amount'].astype(float)
            
            # Format filename with Cambodia timezone
            timestamp = get_cambodia_datetime().strftime('%Y%m%d_%H%M%S')
            safe_title = "".join(c for c in chat_title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"payments_{safe_title}_{period}_{timestamp}.xlsx"
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main payments sheet
                df.to_excel(writer, sheet_name='Payments', index=False)
                
                # Summary sheet
                summary_data = {
                    'Period': [period.title()],
                    'Total USD': [df['usd_amount'].sum()],
                    'Total KHR': [df['riel_amount'].sum()],
                    'Number of Payments': [len(df)],
                    'Export Date': [get_cambodia_datetime().strftime('%Y-%m-%d %H:%M:%S')]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Daily totals sheet
                daily_totals = df.groupby('payment_date').agg({
                    'usd_amount': 'sum',
                    'riel_amount': 'sum'
                }).reset_index()
                daily_totals.to_excel(writer, sheet_name='Daily Totals', index=False)
            
            logger.info(f"Exported {len(payments)} payments to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return None
    
    def get_stats(self, chat_id: int) -> Dict:
        """Get comprehensive statistics."""
        try:
            with self.connection.cursor() as cursor:
                # Get total counts and amounts
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                    FROM payments WHERE chat_id = %s
                """, (chat_id,))
                total_count, total_usd, total_riel = cursor.fetchone()
                
                # Get today's stats
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