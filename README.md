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

- **USD**: `$10.50`, `$1,200.25`
- **Cambodian Riel**: `៛25,000`, `៛500,000`

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

## Installation

### Prerequisites

- Python 3.7+
- PostgreSQL database
- Telegram bot token (from @BotFather)

### Dependencies

```bash
pip install python-telegram-bot python-dotenv apscheduler psycopg2-binary pandas openpyxl
```

### Setup

1. **Create a Telegram Bot**:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token

2. **Configure Environment**:
   Create a `.env` file:
   ```
   BOT_TOKEN=your_bot_token_here
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

3. **Database Setup**:
   - Ensure PostgreSQL is running
   - The bot will automatically create required tables

4. **Group Privacy Settings** (Important for Groups):
   - Go to @BotFather
   - Send `/mybots`
   - Select your bot
   - Go to "Bot Settings" → "Group Privacy"
   - Select "Disable"

### Running the Bot

```bash
python main.py
```

## File Structure

```
telegram-payment-bot/
├── main.py                 # Entry point and bot initialization
├── bot_handlers.py         # Telegram message and command handlers
├── currency_extractor.py   # Currency detection and parsing logic
├── database.py            # PostgreSQL database operations
├── .env                   # Environment configuration (create this)
├── requirements.txt       # Python dependencies
└── README.md             # This documentation
```

## Architecture

### Core Components

1. **Main Application** (`main.py`)
   - Bot initialization and configuration
   - Logging setup
   - Scheduler for maintenance tasks

2. **Bot Handlers** (`bot_handlers.py`)
   - All Telegram command and message handlers
   - Error handling and user feedback
   - Group privacy detection and guidance

3. **Currency Extraction** (`currency_extractor.py`)
   - Regex-based currency amount detection
   - Database integration for payment storage
   - Export functionality interface

4. **Database Operations** (`database.py`)
   - PostgreSQL connection management
   - Payment record CRUD operations
   - Time-based query functions
   - Excel export generation

### Data Flow

1. **Message Reception**: Telegram sends messages to bot
2. **Currency Detection**: Regex patterns identify payment amounts
3. **Database Storage**: Payment records stored with metadata
4. **User Queries**: Commands trigger database queries for totals
5. **Report Generation**: Excel exports created from database data

## Database Schema

### payments table
- `id` (SERIAL PRIMARY KEY)
- `user_id` (BIGINT) - Telegram user ID
- `username` (VARCHAR) - Telegram username
- `chat_id` (BIGINT) - Telegram chat ID
- `chat_title` (VARCHAR) - Chat/group name
- `message_text` (TEXT) - Original message content
- `usd_amount` (DECIMAL) - USD amount detected
- `riel_amount` (DECIMAL) - KHR amount detected
- `payment_date` (DATE) - Date of payment
- `created_at` (TIMESTAMP) - Record creation time

## Usage Examples

### In Group Chats

After disabling bot privacy, the bot will automatically detect:

```
User: "I paid $25.50 for lunch today"
Bot: 💰 Detected: $25.50 USD
     📊 Today's Total: $25.50 USD + ៛0.00 KHR

User: "Taxi cost ៛15,000"
Bot: 💰 Detected: ៛15,000.00 KHR
     📊 Today's Total: $25.50 USD + ៛15,000.00 KHR
```

### Command Usage

```
/total          # Show today's totals
/week           # Show this week's totals
/month          # Show this month's totals
/export month   # Download Excel file with monthly data
/test I paid $50 for dinner  # Test detection without saving
```

## Troubleshooting

### Bot Not Detecting Messages in Groups

**Problem**: Bot shows $0.00 even when payment messages are sent
**Solution**: Disable bot privacy settings via @BotFather

### Database Connection Issues

**Problem**: Database connection errors
**Solution**: 
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Ensure database exists and user has permissions

### Currency Not Detected

**Problem**: Valid amounts not being tracked
**Solution**: Use `/test` command to verify detection patterns

## Development

### Adding New Currencies

1. Update regex patterns in `currency_extractor.py`
2. Modify database schema if needed
3. Update display formatting functions

### Adding New Commands

1. Create handler function in `bot_handlers.py`
2. Register handler in `setup_handlers()`
3. Update help documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review bot logs for error details
3. Verify environment configuration
4. Test with `/test` command for detection issues

---

**Note**: Always keep your bot token secure and never commit it to version control.