# System Patterns: Lector Bot

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      index.py (Entry Point)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    cogs/lector.py (Commands)                 │
│  - Discord commands (lectionary, subscribe, time, etc.)      │
│  - Task loop for scheduled delivery                          │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│  lectionary/registry.py  │  │  helpers/repositories.py     │
│  - Singleton registry    │  │  - GuildSettingsRepository   │
│  - Alias mapping         │  │  - SubscriptionsRepository   │
│  - Cache management      │  │  - Database abstraction      │
└──────────────────────────┘  └──────────────────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│   lectionary/*.py        │  │  helpers/bot_database.py     │
│   - ArmenianLectionary   │  │  - Connection pool           │
│   - CatholicLectionary   │  │  - PostgreSQL connection     │
│   - etc.                 │  └──────────────────────────────┘
└──────────────────────────┘
            │
            ▼
┌──────────────────────────┐
│   lectionary/base.py     │
│   - Abstract base class  │
│   - Common attributes    │
│   - fetch_and_parse_html │
└──────────────────────────┘
```

## Key Design Patterns

### 1. Registry Pattern (lectionary/registry.py)
- Single source of truth for lectionary instances
- Centralized alias-to-index mapping
- Cache management with 1-hour TTL

```python
from lectionary.registry import registry

index = registry.get_index('armenian')  # Returns 0
lec = registry.get(index)  # Returns cached or regenerated instance
```

### 2. Repository Pattern (helpers/repositories.py)
- Abstracts all database operations
- Context manager for safe cursor handling
- Typed methods for each operation

```python
from helpers.repositories import GuildSettingsRepository, SubscriptionsRepository

GuildSettingsRepository.set_time(guild_id, 8)
subs = SubscriptionsRepository.get_for_hour(8)
```

### 3. Template Method Pattern (lectionary/base.py)
- Abstract `Lectionary` base class
- Concrete classes implement: `regenerate()`, `build_json()`, `extract_*()` methods
- Base class provides: `fetch_and_parse_html()`, common attributes

### 4. Cog Pattern (Discord.py)
- `LectionaryCog` groups related commands
- Event listeners for `on_ready`, `on_command_error`
- Task loop for scheduled subscriptions

## Component Relationships

### Lectionary Classes
All inherit from `lectionary/base.py`:
- `ArmenianLectionary`
- `BookOfCommonPrayer`
- `CatholicLectionary` (also has `CatholicPage` helper)
- `OrthodoxAmericanLectionary`
- `OrthodoxCopticLectionary`
- `OrthodoxRussianLectionary`
- `RevisedCommonLectionary` (disabled)

### Helper Modules
- `helpers/bible_url.py`: Convert Bible refs to BibleGateway links
- `helpers/bible_reference.py`: Normalize book abbreviations
- `helpers/date_expand.py`: Format dates with ordinals
- `helpers/logger.py`: Logging utilities

## Critical Implementation Paths

### Fetching a Lectionary
1. User sends `!lectionary armenian`
2. `LectionaryCog.lectionary()` calls `registry.get_index('armenian')`
3. `registry.get(0)` checks cache, regenerates if stale
4. Lectionary fetches HTML, parses readings
5. `build_json()` creates Discord embed data
6. Cog sends embed to channel

### Scheduled Delivery
1. `fulfill_subscriptions` task runs every 10 minutes
2. Checks if current hour needs fulfillment
3. Calls `registry.regenerate_all()` to refresh data
4. Gets subscriptions for current hour via repository
5. Sends embeds to each subscribed channel

### Adding a Subscription
1. Admin sends `!subscribe armenian #channel`
2. Cog validates lectionary name via registry
3. Ensures guild has settings entry
4. Checks subscription limit (max 10 per guild)
5. Adds subscription via repository

