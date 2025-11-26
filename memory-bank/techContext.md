# Technical Context: Lector Bot

## Technologies Used

### Core Stack
- **Python 3.11**: Primary language
- **discord.py 2.2.3**: Discord API wrapper
- **PostgreSQL**: Database for guild settings and subscriptions
- **psycopg2**: PostgreSQL adapter

### Web Scraping
- **requests**: HTTP client for fetching lectionary pages
- **BeautifulSoup4**: HTML parsing

### Utilities
- **python-dotenv**: Environment variable management
- **num2words**: Number formatting (ordinals)

## Development Setup

### Prerequisites
```bash
# Python 3.11+
# PostgreSQL database
# Discord bot token
```

### Environment Variables (.env)
```
token=<discord_bot_token>
prefix=!
DATABASE_URL=postgres://user:pass@host:port/db
log_webhook=<optional_webhook_url>
```

### Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python index.py
```

### Running Tests
```bash
python -m unittest tests.tests -v
```

## Technical Constraints

### Discord API
- Embed title max length: 256 characters
- Rate limits on message sending
- Bot requires `message_content` intent

### Web Scraping
- All HTTP calls are synchronous (blocking)
- Some lectionary sites may change structure
- Network failures must be handled gracefully

### Database
- PostgreSQL required (not SQLite)
- Connection pooling via psycopg2
- Foreign key cascade deletes for cleanup

## Dependencies (requirements.txt)
```
beautifulsoup4==4.12.2
discord.py==2.2.3
psycopg2==2.9.6
python-dotenv==1.0.0
requests==2.30.0
num2words==0.5.12
```

## Deployment
- Procfile for Heroku/similar platforms
- Dockerfile available for containerization
- runtime.txt specifies Python version

