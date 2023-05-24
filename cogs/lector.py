import datetime
import re
import typing

import discord
from discord.ext import commands, tasks

from helpers import logger
from helpers.bot_database import db
from lectionary.armenian import ArmenianLectionary
from lectionary.bcp import BookOfCommonPrayer
from lectionary.catholic import CatholicLectionary
from lectionary.orthodox_american import OrthodoxAmericanLectionary
from lectionary.orthodox_coptic import OrthodoxCopticLectionary
from lectionary.orthodox_greek import OrthodoxGreekLectionary
from lectionary.orthodox_russian import OrthodoxRussianLectionary
from lectionary.rcl import RevisedCommonLectionary

logger = logger.get_logger(__name__)


class Lectionary(commands.Cog):
    MAX_SUBSCRIPTIONS = 10
    EARLIEST_TIME = 7
    LATEST_TIME = 23

    def __init__(self, bot):
        self.last_fulfill = None
        self.lectionaries = None
        self.lectionary_names = None
        self.bot = bot

        self._init_lectionaries()

        self._init_sql_commands()

        self._start_event_loop()

        logger.debug(f'Bot booted. Will not fulfill subscriptions for {self.last_fulfill}:00 GMT or prior.')

    def _start_event_loop(self):
        # Start up the event loop
        self.last_fulfill = datetime.datetime.utcnow().hour
        self.fulfill_subscriptions.start()

    @staticmethod
    def _init_sql_commands():
        logger.debug('Initial data fetch')
        # Initialize the database if it's not ready
        conn = db.get_conn()
        c = conn.cursor()
        try:
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
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

        finally:
            db.put_conn(conn)

    def _init_lectionaries(self):
        # This list is for indexing-display purposes
        self.lectionary_names = [
            'armenian',
            'book of common prayer',
            'catholic',
            'america orthodox',
            'coptic orthodox',
            'greek orthodox',
            'russian orthodox',
            'revised common']
        # Lectionary Objects
        self.lectionaries = [
            ArmenianLectionary(),
            BookOfCommonPrayer(),
            CatholicLectionary(),
            OrthodoxAmericanLectionary(),
            OrthodoxCopticLectionary(),
            OrthodoxGreekLectionary(),
            OrthodoxRussianLectionary(),
            RevisedCommonLectionary()]

    def regenerate_all(self):
        for index in range(len(self.lectionaries)):
            self.lectionaries[index].regenerate()
        logger.debug('Refetched lectionary data')

    @staticmethod
    def _index_lectionary_name(lectionary):
        """
        Given a lectionary name (str), returns its index number (int).
        If the name is invalid, -1 is returned.
        """

        indexes = {
            'armenian': 0, 'a': 0,
            'book of common prayer': 1, 'bcp': 1, 'b': 1,
            'catholic': 2, 'c': 2,
            'american orthodox': 3, 'ao': 3, "oca": 3,
            'coptic orthodox': 4, 'co': 4,
            'greek orthodox': 5, 'go': 5,
            'russian orthodox': 6, 'ro': 6,
            'revised common': 7, 'rcl': 7, 'r': 7
        }

        if lectionary in indexes:
            return indexes[lectionary]
        else:
            return -1

    '''LECTIONARY REQUEST COMMAND'''

    @commands.command(aliases=['l'])
    async def lectionary(self, ctx, *lec):
        lec = self._validate_lectionary_input(lec)
        if lec is None:
            await ctx.send('You didn\'t specify a lectionary.\n\nCurrent options are:\n'
                           '\"Armenian\" (shortcut `a`)\n'
                           '\"Book of Common Prayer\" (shortcut `bcp` or `b`)\n'
                           '\"Catholic\" (shortcut `c`)\n'
                           '\"American Orthodox\" (shortcut `ao` or `oca`)\n'
                           '\"Coptic Orthodox\" (shortcut `co`)\n'
                           '\"Greek Orthodox\" (shortcut `go`)\n'
                           '\"Russian Orthodox\" (shortcut `ro`)\n'
                           '\"Revised Common\" (shortcut `rcl` or `r`)\n'
                           )
            return

        index = self._index_lectionary_name(lec)

        if index > -1:
            lectionary = self._get_or_regenerate_lectionary(index)
            if lectionary is None:
                await ctx.message.add_reaction('❌')
                await ctx.send("Lectionary failed. Please report to the bot owner (@Tarkavor) for assistance.")
                return

            await self.send_lectionary(ctx, lectionary)
        else:
            await ctx.send('You didn\'t specify a valid lectionary.\n\nCurrent options are:\n'
                           '\"Armenian\" (shortcut `a`)\n'
                           '\"Book of Common Prayer\" (shortcut `bcp` or `b`)\n'
                           '\"Catholic\" (shortcut `c`)\n'
                           '\"American Orthodox\" (shortcut `ao` or `oca`)\n'
                           '\"Coptic Orthodox\" (shortcut `co`)\n'
                           '\"Greek Orthodox\" (shortcut `go`)\n'
                           '\"Russian Orthodox\" (shortcut `ro`)\n'
                           '\"Revised Common\" (shortcut `rcl` or `r`)\n'
                           )

    @staticmethod
    def _validate_lectionary_input(lec):
        if lec is None:
            return None
        return ' '.join(lec).lower()

    def _get_or_regenerate_lectionary(self, index):
        if not self.lectionaries[index].ready:
            self.lectionaries[index].regenerate()
            if not self.lectionaries[index].ready:
                print('Lectionary not regenerated correctly.')
                return None
        return self.lectionaries[index]

    @staticmethod
    async def send_lectionary(ctx, lectionary):
        for piece in lectionary.build_json():
            await ctx.send(embed=discord.Embed.from_dict(piece))

    '''SUBSCRIPTION COMMANDS'''

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def time(self, ctx, *, time=''):
        if time == '':
            await self._send_current_time(ctx)
        else:
            await self._update_guild_time(ctx, time)

    @staticmethod
    async def _send_current_time(ctx):
        now = datetime.datetime.utcnow()
        output = now.strftime(f'It is currently: %A, %B {now.day}, %Y, %I:%M:%S %p (GMT).')
        await ctx.send(output)

    async def _update_guild_time(self, ctx, time):
        time = self._parse_time(time)
        if time is not None:
            guild_id = ctx.guild.id
            self._update_guild_settings(guild_id, time)
            await ctx.send(f'The guild\'s subscriptions will come {time}:00 GMT daily.')
        else:
            await ctx.send('You didn\'t specify a valid time.')

    def _parse_time(self, time):
        # If the user specified an integer, it's possibly 24-hour time
        if time in re.findall(r'[0-9]+', time):
            time = int(time)
        # If a meridiem was possibly specified
        else:
            time = time.lower()
            match = re.search(r'([0-9]+) *(am|pm)', time)
            if match:
                time = int(match.group(1))
                if match.group(2) == 'pm': time += 12
            else:
                return None

        if not (self.EARLIEST_TIME <= time <= self.LATEST_TIME):
            return None

        return time

    @staticmethod
    def _update_guild_settings(guild_id, time):
        conn = db.get_conn()
        c = conn.cursor()
        try:
            c.execute('SELECT * FROM GuildSettings WHERE guild_id = %s', (guild_id,))
            setting = c.fetchone()
            if setting:
                c.execute('UPDATE GuildSettings SET time = %s WHERE guild_id = %s', (time, guild_id))
            else:
                c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (guild_id, time))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            db.put_conn(conn)

    @commands.command(aliases=['sub'])
    @commands.has_permissions(manage_messages=True)
    async def subscribe(self, ctx, lectionary=None, channel: typing.Optional[discord.TextChannel] = None):
        if lectionary is None:
            await ctx.send(embed=self._build_subscriptions_list(ctx))
            return

        sub_type = self._index_lectionary_name(lectionary)

        if sub_type == -1:
            await ctx.send('You didn\'t specify a valid lectionary option.')
            return

        channel_id = self._get_channel_id(ctx, channel)
        guild_id = ctx.guild.id

        self._check_or_create_guild(guild_id)
        await self._check_subscription_and_add(ctx, channel_id, sub_type, guild_id)

    @staticmethod
    def _get_channel_id(ctx, channel):
        if channel:
            return channel.id
        else:
            return ctx.channel.id

    def _check_or_create_guild(self, guild_id):
        conn = db.get_conn()
        c = conn.cursor()
        try:
            # Check to see if the guild has a settings entry yet
            c.execute('SELECT * FROM GuildSettings WHERE guild_id = %s', (guild_id,))
            row = c.fetchone()
            if not row:
                # If not, create a default entry for the guild
                c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (guild_id, self.EARLIEST_TIME))
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            db.put_conn(conn)

    async def _check_subscription_and_add(self, ctx, channel_id, sub_type, guild_id):
        conn = db.get_conn()
        c = conn.cursor()
        try:
            # Check if the given channel is already subscribed to the given lectionary
            c.execute('SELECT * FROM Subscriptions WHERE channel_id=%s AND sub_type=%s', (channel_id, sub_type))
            row = c.fetchone()
            sub_name = self.lectionary_names[sub_type].title()
            if row:
                await ctx.send(f'<#{channel_id}> is already subscribed to the {sub_name} lectionary.')
            else:
                # Check to make sure there aren't too many subscriptions already
                c.execute('SELECT COUNT(guild_id) FROM Subscriptions WHERE guild_id=%s', (guild_id,))
                if c.fetchone()[0] >= self.MAX_SUBSCRIPTIONS:
                    await ctx.send(f'You can\'t have more than {self.MAX_SUBSCRIPTIONS} subscriptions per guild.')
                else:
                    c.execute('INSERT INTO Subscriptions VALUES (%s, %s, %s)', (guild_id, channel_id, sub_type))
                    conn.commit()
                    await ctx.send(f'<#{channel_id}> has been subscribed to the {sub_name} lectionary.')
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            db.put_conn(conn)

    @commands.command(aliases=['unsub'])
    @commands.has_permissions(manage_messages=True)
    async def unsubscribe(self, ctx, channel: discord.TextChannel = None, lectionary: str = None):
        conn = db.get_conn()
        c = conn.cursor()

        try:
            if (channel is None) and (lectionary is None):
                # Remove all the guild's subscriptions
                c.execute('DELETE FROM GuildSettings WHERE guild_id = %s', (ctx.guild.id,))
                await ctx.send(f'All subscriptions for {ctx.guild.name} have been removed.')

            elif isinstance(channel, discord.TextChannel):
                # Remove all subscriptions for the given channel
                channel_id = channel.id

                if lectionary is None:
                    c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))
                    await ctx.send(f'<#{channel_id}> has been unsubscribed from all lectionaries.')
                else:
                    sub_type = self._index_lectionary_name(lectionary)

                    if sub_type == -1:
                        await ctx.send('You didn\'t specify a valid lectionary option.')
                        return

                    c.execute('DELETE FROM Subscriptions WHERE channel_id = %s AND sub_type = %s',
                              (channel_id, sub_type))
                    await ctx.send(
                        f'<#{channel_id}> has been unsubscribed from the {self.lectionary_names[sub_type].title()} lectionary.')

            else:
                await ctx.send('You didn\'t specify a valid unsubscription option.')
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            db.put_conn(conn)

    def _build_subscriptions_list(self, ctx):
        """
        Helper method to generate an embed listing the subscriptions for a
        guild given the guild id.
        """
        time, subscriptions = self._get_subscriptions(ctx)
        embed = self._create_embed(ctx, time, subscriptions)
        return embed

    def _get_subscriptions(self, ctx):
        conn = db.get_conn()
        c = conn.cursor()
        try:
            c.execute('SELECT time FROM GuildSettings WHERE guild_id = %s', (ctx.guild.id,))
            time = c.fetchone()
            if not time:
                time = self.EARLIEST_TIME
                c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (ctx.guild.id, time))
                conn.commit()

            c.execute('SELECT * FROM Subscriptions WHERE guild_id = %s', (ctx.guild.id,))
            subscriptions = c.fetchall()
            conn.commit()

        except Exception as e:
            conn.rollback()
            # You should log the exception here
            raise e

        finally:
            db.put_conn(conn)

        return time, subscriptions

    def _create_embed(self, ctx, time, subscriptions):
        embed = discord.Embed(title=f'Subscriptions for {ctx.guild.name}')
        if subscriptions:
            embed.description = ''
            for subscription in subscriptions:
                channel_id = subscription[1]
                sub_name = self.lectionary_names[subscription[2]].title()
                embed.description += f'\n<#{channel_id}> - {sub_name} lectionary'

            embed.set_footer(text=f'(Daily @ {time}:00 GMT)')
        else:
            embed.description = 'There are none'

        return embed

    '''SYSTEM COMMANDS'''

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """
        Command to safely shutdown the bot with a reduced chance of
        damaging the database. (Bot owner only.)
        """
        try:
            self.fulfill_subscriptions.stop()
            await ctx.message.add_reaction('✅')
            logger.debug('Shutdown request, logging out')
            await ctx.bot.close()
        except Exception as e:
            logger.debug('An error occurred during shutdown: ' + str(e))
            await ctx.send(f'An error occurred during shutdown: {e}')

    @commands.command()
    @commands.is_owner()
    async def push(self, ctx, current_hour: int = datetime.datetime.utcnow().hour):
        logger.debug(f'Manual subscription push requested for {current_hour}:00 GMT')

        try:
            if self.EARLIEST_TIME <= current_hour <= self.LATEST_TIME:
                # Regenerate all if it's the earliest time
                if current_hour == self.EARLIEST_TIME:
                    self.regenerate_all()

                await ctx.message.add_reaction('✅')
                await self.push_subscriptions(current_hour)
            else:
                await ctx.message.add_reaction('❌')
                logger.debug(f'Push failed. current_hour={current_hour} is outside the acceptable range.')
        except Exception as e:
            logger.debug(f'An error occurred during push: {e}')
            await ctx.send(f'An error occurred during push: {e}')

    '''SUBSCRIPTIONS TASK LOOP'''

    @tasks.loop(minutes=10)
    async def fulfill_subscriptions(self):
        # Push the current hour's subscriptions if they haven't been already
        current_hour = datetime.datetime.utcnow().hour

        if (self.EARLIEST_TIME <= current_hour <= self.LATEST_TIME) and (self.last_fulfill != current_hour):
            logger.debug(f"Starting to fulfill subscriptions for {current_hour} hour")
            # Make sure the lectionary embeds are updated for the day
            if current_hour == self.EARLIEST_TIME:
                self.regenerate_all()

            try:
                await self.push_subscriptions(current_hour)
                self.last_fulfill = current_hour
                logger.debug(f"Successfully fulfilled subscriptions for {current_hour} hour")
            except Exception as e:
                logger.debug(f"Error during fulfilling subscriptions for {current_hour} hour: {e}")

    @fulfill_subscriptions.before_loop
    async def before_fulfill_subscriptions(self):
        await self.bot.wait_until_ready()

    '''SUBSCRIPTIONS HELPER METHODS'''

    async def _remove_deleted_guilds(self):
        """
        Helper method to purge the settings of deleted guilds from
        the database. The ON CASCADE DELETE option in the database
        also makes this wipe the subscriptions automatically.
        """
        conn = db.get_conn()
        c = conn.cursor()
        try:
            c.execute('SELECT guild_id FROM GuildSettings')
            guild_ids = [item[0] for item in c.fetchall()]

            total = len(guild_ids)

            logger.debug(f"Checking {total} guilds for deletion")

            deleted_guild_ids = [guild_id for guild_id in guild_ids if not self.bot.get_guild(guild_id)]

            count = len(deleted_guild_ids)

            if deleted_guild_ids:
                # Create query for batch deletion
                query = "DELETE FROM GuildSettings WHERE guild_id IN %s"
                c.execute(query, (tuple(deleted_guild_ids),))

                conn.commit()

                logger.debug(f'Purged {count} out of {total} guilds')

        except Exception as e:
            conn.rollback()
            logger.debug(f"Error during guild purge: {e}")
            raise e

        finally:
            db.put_conn(conn)

    async def push_subscriptions(self, hour):
        await self._remove_deleted_guilds()
        conn = db.get_conn()
        c = conn.cursor()
        try:
            # Get all subscriptions for the guilds that have their time preference
            # set to the given hour
            c.execute('''
                SELECT Subscriptions.channel_id, Subscriptions.sub_type
                FROM Subscriptions
                INNER JOIN GuildSettings
                ON Subscriptions.guild_id = GuildSettings.guild_id
                WHERE GuildSettings.time = %s
            ''', (hour,))

            subscriptions = c.fetchall()
            total_subs = len(subscriptions)
            successful_subs = 0

            if total_subs > 0:
                logger.debug(f"Preparing to push {total_subs} subscription(s) for {hour}:00 GMT")

            # Each subscription is a tuple: (channel_id, sub_type)
            for subscription in subscriptions:
                channel_id = subscription[0]
                sub_type = subscription[1]
                channel = self.bot.get_channel(channel_id)

                if channel:
                    feed = self.lectionaries[sub_type].build_json()
                    for item in feed:
                        await channel.send(embed=discord.Embed.from_dict(item))
                    successful_subs += 1
                else:
                    c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))

            conn.commit()

            if successful_subs > 0:
                logger.debug(
                    f'Successfully pushed {successful_subs} out of {total_subs} subscriptions for {hour}:00 GMT')

        except Exception as e:
            conn.rollback()
            logger.debug(f"Error while pushing subscriptions for {hour}:00 GMT: {e}")
            raise e

        finally:
            db.put_conn(conn)


async def setup(bot):
    await bot.add_cog(Lectionary(bot))
