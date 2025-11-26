# Project Brief: Lector Discord Bot

## Overview
Lector is a Discord bot that fetches and delivers daily Bible readings from various Christian lectionaries. It supports subscription-based automatic delivery to Discord channels at scheduled times.

## Core Requirements

### Functional Requirements
1. **Lectionary Fetching**: Scrape daily readings from multiple lectionary sources
2. **Discord Integration**: Deliver readings as rich embeds in Discord channels
3. **Subscription System**: Allow guilds to subscribe channels to specific lectionaries
4. **Scheduling**: Deliver subscribed readings at configurable times (hourly, 0-23 GMT)

### Supported Lectionaries
- Armenian Lectionary (armenianscripture.wordpress.com)
- Book of Common Prayer (biblegateway.com)
- Catholic/USCCB (bible.usccb.org)
- American Orthodox/OCA (oca.org)
- Coptic Orthodox (copticchurch.net)
- Russian Orthodox (holytrinityorthodox.com)
- Greek Orthodox (disabled)
- Revised Common Lectionary (disabled)

### Non-Functional Requirements
- Handle network failures gracefully
- Cache lectionary data for 1 hour to reduce scraping
- Support multiple guilds with independent settings
- PostgreSQL database for persistence

## Target Users
- Christian Discord communities
- Churches with Discord servers
- Individuals wanting daily scripture readings

## Success Metrics
- Reliable daily delivery of readings
- Support for 10+ subscriptions per guild
- Clean, readable embed formatting with Bible Gateway links

