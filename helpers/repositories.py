"""
Database repository classes for guild settings and subscriptions.

This module provides a clean abstraction over the database operations,
replacing raw SQL scattered throughout the cog file.
"""
from contextlib import contextmanager
from typing import List, Optional, Tuple

from helpers.bot_database import db
from helpers.logger import get_logger

_logger = get_logger(__name__)


@contextmanager
def get_cursor():
    """
    Context manager for database operations with auto-commit/rollback.
    
    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT ...")
            result = cursor.fetchall()
    """
    conn = db.get_conn()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db.put_conn(conn)


def init_database_schema():
    """
    Initialize database tables if they don't exist.
    
    Creates:
        - GuildSettings: Stores per-guild time preferences
        - Subscriptions: Stores channel subscriptions to lectionaries
    """
    _logger.debug('Initializing database schema')
    with get_cursor() as c:
        # Guild settings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS GuildSettings (
                guild_id BIGINT NOT NULL,
                time     BIGINT NOT NULL,
                PRIMARY KEY (guild_id)
            )
        ''')
        # Subscriptions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS Subscriptions (
                guild_id   BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                sub_type   BIGINT NOT NULL,
                FOREIGN KEY (guild_id) REFERENCES GuildSettings(guild_id) ON DELETE CASCADE
            )
        ''')


class GuildSettingsRepository:
    """Repository for guild settings (time preferences)."""
    
    @staticmethod
    def get_time(guild_id: int) -> Optional[int]:
        """Get the scheduled time for a guild, or None if not set."""
        with get_cursor() as c:
            c.execute('SELECT time FROM GuildSettings WHERE guild_id = %s', (guild_id,))
            row = c.fetchone()
            return row[0] if row else None
    
    @staticmethod
    def set_time(guild_id: int, time: int) -> None:
        """Set or update the scheduled time for a guild."""
        with get_cursor() as c:
            c.execute('SELECT * FROM GuildSettings WHERE guild_id = %s', (guild_id,))
            if c.fetchone():
                c.execute('UPDATE GuildSettings SET time = %s WHERE guild_id = %s', (time, guild_id))
            else:
                c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (guild_id, time))
    
    @staticmethod
    def ensure_exists(guild_id: int, default_time: int = 0) -> None:
        """Ensure a guild has a settings entry, creating one if needed."""
        with get_cursor() as c:
            c.execute('SELECT * FROM GuildSettings WHERE guild_id = %s', (guild_id,))
            if not c.fetchone():
                c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (guild_id, default_time))
    
    @staticmethod
    def delete(guild_id: int) -> None:
        """Delete a guild's settings (cascades to subscriptions)."""
        with get_cursor() as c:
            c.execute('DELETE FROM GuildSettings WHERE guild_id = %s', (guild_id,))
    
    @staticmethod
    def get_all_guild_ids() -> List[int]:
        """Get all guild IDs that have settings."""
        with get_cursor() as c:
            c.execute('SELECT guild_id FROM GuildSettings')
            return [row[0] for row in c.fetchall()]
    
    @staticmethod
    def delete_many(guild_ids: List[int]) -> int:
        """Delete multiple guilds by ID. Returns count deleted."""
        if not guild_ids:
            return 0
        with get_cursor() as c:
            c.execute("DELETE FROM GuildSettings WHERE guild_id IN %s", (tuple(guild_ids),))
            return len(guild_ids)


class SubscriptionsRepository:
    """Repository for channel subscriptions to lectionaries."""
    
    @staticmethod
    def get_for_guild(guild_id: int) -> List[Tuple[int, int, int]]:
        """
        Get all subscriptions for a guild.
        
        Returns:
            List of tuples: (guild_id, channel_id, sub_type)
        """
        with get_cursor() as c:
            c.execute('SELECT * FROM Subscriptions WHERE guild_id = %s', (guild_id,))
            return c.fetchall()
    
    @staticmethod
    def get_for_hour(hour: int) -> List[Tuple[int, int]]:
        """
        Get all subscriptions scheduled for a specific hour.
        
        Returns:
            List of tuples: (channel_id, sub_type)
        """
        with get_cursor() as c:
            c.execute('''
                SELECT Subscriptions.channel_id, Subscriptions.sub_type
                FROM Subscriptions
                INNER JOIN GuildSettings
                ON Subscriptions.guild_id = GuildSettings.guild_id
                WHERE GuildSettings.time = %s
            ''', (hour,))
            return c.fetchall()
    
    @staticmethod
    def exists(channel_id: int, sub_type: int) -> bool:
        """Check if a specific subscription already exists."""
        with get_cursor() as c:
            c.execute('SELECT * FROM Subscriptions WHERE channel_id=%s AND sub_type=%s', 
                      (channel_id, sub_type))
            return c.fetchone() is not None
    
    @staticmethod
    def count_for_guild(guild_id: int) -> int:
        """Count total subscriptions for a guild."""
        with get_cursor() as c:
            c.execute('SELECT COUNT(guild_id) FROM Subscriptions WHERE guild_id=%s', (guild_id,))
            return c.fetchone()[0]
    
    @staticmethod
    def add(guild_id: int, channel_id: int, sub_type: int) -> bool:
        """
        Add a subscription if it doesn't already exist.
        
        Returns:
            True if added, False if already exists
        """
        if SubscriptionsRepository.exists(channel_id, sub_type):
            return False
        with get_cursor() as c:
            c.execute('INSERT INTO Subscriptions VALUES (%s, %s, %s)', 
                      (guild_id, channel_id, sub_type))
        return True
    
    @staticmethod
    def delete_for_channel(channel_id: int, sub_type: Optional[int] = None) -> None:
        """
        Delete subscriptions for a channel.
        
        Args:
            channel_id: The channel to unsubscribe
            sub_type: If provided, only delete this specific subscription type.
                      If None, delete all subscriptions for the channel.
        """
        with get_cursor() as c:
            if sub_type is None:
                c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))
            else:
                c.execute('DELETE FROM Subscriptions WHERE channel_id = %s AND sub_type = %s',
                          (channel_id, sub_type))
    
    @staticmethod
    def delete_by_channel_id(channel_id: int) -> None:
        """Delete all subscriptions for a channel (used when channel is deleted)."""
        with get_cursor() as c:
            c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))

