# Telegram Payment Tracking Bot

A comprehensive Telegram bot that automatically extracts and tracks payment amounts from chat messages with persistent PostgreSQL database storage, multi-currency support, and Excel export functionality.

## Features

- **Automatic Payment Detection**: Detects USD ($) and Cambodian Riel (៛) amounts from messages
- **Persistent Database Storage**: PostgreSQL backend for reliable data persistence
- **Multi-Chat Support**: Isolated payment tracking per chat group
- **Time-Based Reporting**: Daily, weekly, monthly, and yearly totals
- **Excel Export**: Download payment data as Excel files
- **Comprehensive Logging**: Detailed application and database logging

## Supported Currency Formats

- **USD**: $10.50, $1,200.25
- **Cambodian Riel**: ៛25,000, ៛500,000

## Bot Commands

- `/start` - Welcome message and setup instructions
- `/help` - Show available commands
- `/total` - Show today's totals
- `/week` - Show weekly totals
- `/month` - Show monthly totals
- `/year` - Show yearly totals
- `/summary` - Detailed daily summary
- `/export [period]` - Export to Excel (week/month/year/all)
- `/test <message>` - Test payment detection on a message

## How It Works

1. **Automatic Detection**: Send any message containing payment amounts
2. **Multi-Currency Support**: Detects both USD and Cambodian Riel in various formats
3. **Instant Confirmation**: Bot confirms detected payments immediately
4. **Persistent Storage**: All payments stored permanently in PostgreSQL
5. **Rich Reporting**: View totals for different time periods
6. **Data Export**: Export payment history to Excel files

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure:
   - `BOT_TOKEN`: Your Telegram bot token from @BotFather
   - `DATABASE_URL`: PostgreSQL connection string
4. Run: `python main.py`

## Deployment

### Railway Deployment
1. Upload all files to GitHub repository
2. Connect repository to Railway
3. Add PostgreSQL database service
4. Set environment variables:
   - `BOT_TOKEN`: Your Telegram bot token
   - `DATABASE_URL`: Automatically provided by Railway PostgreSQL
5. Deploy!

### Environment Variables
- `BOT_TOKEN`: Telegram bot token (required)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `DEBUG`: Enable debug logging (optional)

## Usage Examples

### Automatic Detection
Just send messages with payment amounts:
- "I paid $50 for lunch" → Detects $50
- "Received ៛100,000 payment" → Detects ៛100,000
- "Transfer $25.50 to John" → Detects $25.50

### Commands
- `/total` → Shows today's totals
- `/week` → Shows weekly totals
- `/export month` → Downloads monthly Excel report
- `/test I paid $100` → Tests detection on sample text

## Technical Details

- **Language**: Python 3.11+
- **Framework**: python-telegram-bot 20.8
- **Database**: PostgreSQL with psycopg2
- **Timezone**: Cambodia timezone (UTC+7) for accurate date tracking
- **Export**: pandas + openpyxl for Excel generation
- **Logging**: Comprehensive logging to file and console

## File Structure

```
new_payment_bot/
├── main.py              # Main application entry point
├── database.py          # PostgreSQL database operations
├── currency_detector.py # Currency extraction logic
├── handlers.py          # Telegram bot handlers
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── Procfile            # Railway/Heroku deployment
├── runtime.txt         # Python version specification
└── README.md           # This file
```

## License

MIT License - feel free to use and modify as needed.