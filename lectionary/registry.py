"""
Centralized lectionary management and caching.

This module provides a single registry for all lectionary instances,
replacing the scattered initialization and lookup logic in the cog.
"""
import datetime
from typing import Optional, Dict, List

from helpers.logger import get_logger
from lectionary.base import Lectionary
from lectionary.armenian import ArmenianLectionary
from lectionary.bcp import BookOfCommonPrayer
from lectionary.catholic import CatholicLectionary
from lectionary.orthodox_american import OrthodoxAmericanLectionary
from lectionary.orthodox_coptic import OrthodoxCopticLectionary
from lectionary.orthodox_russian import OrthodoxRussianLectionary
# from lectionary.orthodox_greek import OrthodoxGreekLectionary  # Currently disabled
# from lectionary.rcl import RevisedCommonLectionary  # Currently disabled

_logger = get_logger(__name__)


class LectionaryRegistry:
    """
    Manages lectionary instances with caching and lazy regeneration.
    
    This class centralizes:
    - Lectionary instantiation
    - Name/alias to index mapping
    - Cache management (regenerate if stale or not ready)
    """
    
    # Centralized name-to-index mapping (single source of truth)
    # Note: Indices must match the order in _instances list
    ALIASES: Dict[str, int] = {
        'armenian': 0, 'a': 0,
        'book of common prayer': 1, 'bcp': 1, 'b': 1,
        'catholic': 2, 'c': 2,
        'american orthodox': 3, 'ao': 3, 'oca': 3,
        'coptic orthodox': 4, 'co': 4,
        # 'greek orthodox': 5, 'go': 5,  # Disabled
        'russian orthodox': 5, 'ro': 5,
        # 'revised common': 6, 'rcl': 6, 'r': 6,  # Disabled
    }
    
    # Display names for subscriptions list (matches index order)
    NAMES: List[str] = [
        'armenian',
        'book of common prayer',
        'catholic',
        'america orthodox',  # Note: matches original spelling
        'coptic orthodox',
        # 'greek orthodox',  # Disabled
        'russian orthodox',
        # 'revised common',  # Disabled
    ]
    
    # Cache duration - regenerate if older than this
    CACHE_DURATION = datetime.timedelta(hours=1)

    def __init__(self):
        """Initialize all lectionary instances."""
        _logger.debug('Initializing lectionary registry')
        self._instances: List[Lectionary] = [
            ArmenianLectionary(),
            BookOfCommonPrayer(),
            CatholicLectionary(),
            OrthodoxAmericanLectionary(),
            OrthodoxCopticLectionary(),
            # OrthodoxGreekLectionary(),  # Disabled
            OrthodoxRussianLectionary(),
            # RevisedCommonLectionary(),  # Disabled
        ]

    def get_index(self, name: str) -> int:
        """
        Get lectionary index from name or alias.
        
        Args:
            name: Lectionary name or alias (case-insensitive)
            
        Returns:
            Index of the lectionary, or -1 if not found
        """
        return self.ALIASES.get(name.lower(), -1)

    def get_name(self, index: int) -> str:
        """
        Get display name for a lectionary index.
        
        Args:
            index: The lectionary index
            
        Returns:
            Display name, or "Unknown" if invalid index
        """
        if 0 <= index < len(self.NAMES):
            return self.NAMES[index]
        return "Unknown"

    def get(self, index: int) -> Optional[Lectionary]:
        """
        Get lectionary by index, regenerating if stale.
        
        Args:
            index: The lectionary index
            
        Returns:
            The lectionary instance, or None if invalid index or regeneration failed
        """
        if not (0 <= index < len(self._instances)):
            return None
        
        lec = self._instances[index]
        
        if self._needs_regeneration(lec):
            lec.regenerate()
            if not lec.ready:
                _logger.error(f'Lectionary {type(lec).__name__} not regenerated correctly.', exc_info=True)
                return None
        
        return lec

    def _needs_regeneration(self, lec: Lectionary) -> bool:
        """Check if a lectionary needs to be regenerated."""
        if not lec.ready:
            return True
        time_since_regen = datetime.datetime.now() - lec.last_regeneration
        return time_since_regen > self.CACHE_DURATION

    def regenerate_all(self) -> None:
        """Force regeneration of all lectionaries."""
        for lec in self._instances:
            if self._needs_regeneration(lec):
                lec.regenerate()
        _logger.debug('Regenerated all lectionaries')

    @property
    def lectionary_names(self) -> List[str]:
        """Get the list of display names (for backwards compatibility)."""
        return self.NAMES

    @property
    def lectionaries(self) -> List[Lectionary]:
        """Get the list of lectionary instances (for backwards compatibility)."""
        return self._instances


# Singleton instance for use throughout the application
registry = LectionaryRegistry()

