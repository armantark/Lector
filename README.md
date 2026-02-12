# Lector Bot

![version](https://img.shields.io/badge/version-alpha-%23ec4242)
![python](https://img.shields.io/badge/python-3.11-green)
![library](https://img.shields.io/badge/library-discord.py-blue)

Lector is a Discord bot that fetches daily Christian lectionary readings and posts them to Discord channels on demand or on a schedule.

## Features

- Fetch daily readings with simple commands
- Subscribe channels for automatic daily delivery
- Per-guild schedule configuration
- Bible Gateway links for each reading
- Optional combined Bible Gateway link for all references in one page

## Supported Lectionaries

Enabled:

1. Armenian
2. Book of Common Prayer
3. Catholic / USCCB
4. American Orthodox / OCA
5. Coptic Orthodox
6. Russian Orthodox

Disabled (kept in codebase):

1. Greek Orthodox
2. Revised Common Lectionary

## Quick Start

### Requirements

- Python 3.11+
- PostgreSQL
- A Discord bot token

### Environment Variables

Create a `.env` file:

```env
token=<discord_bot_token>
prefix=!
DATABASE_URL=postgres://user:pass@host:port/db
log_webhook=<optional_webhook_url>
```

### Install and Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python index.py
```

### Run Tests

```bash
python -m unittest tests.tests -v
```

## Common Commands

- `!lectionary <name>`
- `!subscribe <name> <#channel>`
- `!unsubscribe <name> <#channel>`
- `!time <hour>`
- `!combinedlinks <on|off>`

## Attribution

The lectionaries are the works of their respective owners.

- [Holy Trinity Russian Orthodox Church](https://www.holytrinityorthodox.com/) provides an [API interface](https://www.holytrinityorthodox.com/calendar/doc/) for integrating their calendar into websites.
- [The Consultation on Common Texts](http://www.commontexts.org/) permits reproductions of the RCL table of citations under [specific conditions](http://www.commontexts.org/rcl/permissions/).

The Lector logo is a cropped version of a [public domain image](https://flic.kr/p/7de5pN) from [Flickr](https://www.flickr.com/).