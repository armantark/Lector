# Active Context: Lector Bot

## Current Work Focus
Major structural refactoring completed. The codebase has been reorganized for better maintainability without changing external behavior.

## Recent Changes

### Completed Refactoring (November 2025)

#### Phase 1: Quick Cleanups
- Renamed `Lectionary` cog class to `LectionaryCog` (fixes naming conflict with base class)
- Fixed logger shadowing in 4 files (armenian.py, catholic.py, orthodox_russian.py, lector.py)
- Removed unused `client` and `tree` variables from index.py

#### Phase 2: Lectionary Standardization
- Renamed `lectionary/lectionary.py` → `lectionary/base.py`
- Made `CatholicLectionary` inherit from base `Lectionary` class
- Made `RevisedCommonLectionary` inherit from base class
- Created `helpers/bible_reference.py` with shared reference normalization

#### Phase 3: Database Abstraction
- Created `helpers/repositories.py` with `GuildSettingsRepository` and `SubscriptionsRepository`
- Migrated all raw SQL from cog to repository methods
- Added `get_cursor()` context manager for safe DB operations

#### Phase 4: Lectionary Registry
- Created `lectionary/registry.py` with `LectionaryRegistry` class
- Centralized alias mapping (single source of truth)
- Moved caching logic from cog to registry

#### Phase 5: Slim Cog
- Reduced `cogs/lector.py` from 597 lines to 401 lines (33% reduction)
- Cog now only contains commands and orchestration

### Test Suite
- Expanded from 2 tests to 106 tests
- Unit tests for all helper modules
- Integration tests for lectionary classes
- E2E tests for full flows
- Mock tests for network error handling
- Regression tests to prevent re-introducing bugs

## Next Steps (Potential Future Work)
1. Convert synchronous HTTP calls to async (aiohttp) for better performance
2. Add more comprehensive test coverage for edge cases
3. Consider migrating to an ORM (SQLAlchemy)
4. Re-enable Greek Orthodox and Revised Common lectionaries when sources stabilize

## Important Patterns and Preferences

### Logging Convention
```python
from helpers.logger import get_logger
_logger = get_logger(__name__)  # Use _logger, not logger
```

### Database Access
Always use repositories, never raw SQL in cogs:
```python
from helpers.repositories import GuildSettingsRepository
GuildSettingsRepository.set_time(guild_id, time)
```

### Lectionary Access
Always use registry, never direct instantiation in cogs:
```python
from lectionary.registry import registry
lec = registry.get(index)
```

## Learnings and Project Insights
- The original `Lectionary` naming conflict (cog vs base class) caused confusion
- Logger module shadowing pattern (`logger = logger.get_logger()`) is an anti-pattern
- `CatholicLectionary` and `RevisedCommonLectionary` were unique in not inheriting from base
- Repository pattern significantly cleans up cog code
- Registry pattern centralizes lectionary management and caching

