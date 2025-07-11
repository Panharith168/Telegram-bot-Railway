"""
Database operations for payment tracking

Handles all database operations including payments, totals, and export functionality.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class PaymentDatabase:
    def __init__(self):
        self.connection = None
        self.connect()
        self.setup_database()
    
    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            # Try DATABASE_URL first (Railway style)
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(database_url)
                self.connection.autocommit = True
                logger.info("Connected to PostgreSQL database via DATABASE_URL")
            else:
                # Fallback to individual environment variables
                self.connection = psycopg2.connect(
                    host=os.getenv('PGHOST'),
                    database=os.getenv('PGDATABASE'),
                    user=os.getenv('PGUSER'),
                    password=os.getenv('PGPASSWORD'),
                    port=os.getenv('PGPORT')
                )
                self.connection.autocommit = True
                logger.info("Connected to PostgreSQL database via individual variables")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            # Log available environment variables for debugging
            logger.error(f"DATABASE_URL available: {bool(os.getenv('DATABASE_URL'))}")
            logger.error(f"PGHOST available: {bool(os.getenv('PGHOST'))}")
            raise
    
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
                      usd_amount, riel_amount, date.today()))
                
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
                if period == 'today':
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date = %s
                    """, (chat_id, date.today()))
                elif period == 'week':
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= CURRENT_DATE - INTERVAL '7 days'
                    """, (chat_id,))
                elif period == 'month':
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= DATE_TRUNC('month', CURRENT_DATE)
                    """, (chat_id,))
                elif period == 'year':
                    cursor.execute("""
                        SELECT COALESCE(SUM(usd_amount), 0), COALESCE(SUM(riel_amount), 0)
                        FROM payments 
                        WHERE chat_id = %s AND payment_date >= DATE_TRUNC('year', CURRENT_DATE)
                    """, (chat_id,))
                
                result = cursor.fetchone()
                return float(result[0]), float(result[1])
        except Exception as e:
            logger.error(f"Failed to get totals: {e}")
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
            # Determine date range based on period
            start_date = None
            end_date = date.today()
            
            if period == 'week':
                start_date = date.today() - pd.Timedelta(days=7)
            elif period == 'month':
                start_date = date.today().replace(day=1)
            elif period == 'year':
                start_date = date.today().replace(month=1, day=1)
            
            # Get payment data
            payments = self.get_payments_for_export(chat_id, start_date, end_date)
            
            if not payments:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(payments)
            df['usd_amount'] = df['usd_amount'].astype(float)
            df['riel_amount'] = df['riel_amount'].astype(float)
            
            # Format filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
                    'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
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
            logger.error(f"Failed to export to Excel: {e}")
            return None
    
    def get_stats(self, chat_id: int) -> Dict:
        """Get comprehensive statistics."""
        try:
            with self.connection.cursor() as cursor:
                # Overall stats
                cursor.execute("""
                    SELECT COUNT(*) as total_payments,
                           COALESCE(SUM(usd_amount), 0) as total_usd,
                           COALESCE(SUM(riel_amount), 0) as total_riel,
                           MIN(payment_date) as first_payment,
                           MAX(payment_date) as last_payment
                    FROM payments WHERE chat_id = %s
                """, (chat_id,))
                
                overall = cursor.fetchone()
                
                return {
                    'total_payments': overall[0],
                    'total_usd': float(overall[1]),
                    'total_riel': float(overall[2]),
                    'first_payment': overall[3],
                    'last_payment': overall[4]
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

# Global database instance
db = None

def get_database():
    """Get database instance."""
    global db
    if db is None:
        db = PaymentDatabase()
    return db