import datetime
import re
import typing

import discord
from discord.ext import commands, tasks

from helpers.logger import get_logger
from helpers.repositories import (
    init_database_schema,
    GuildSettingsRepository,
    SubscriptionsRepository,
)
from lectionary.registry import registry

_logger = get_logger(__name__)


class LectionaryCog(commands.Cog):
    MAX_SUBSCRIPTIONS = 10
    EARLIEST_TIME = 0
    LATEST_TIME = 23

    def __init__(self, bot):
        self.last_fulfill = None
        self.bot = bot

        self._init_sql_commands()
        self._start_event_loop()

        _logger.debug(f'Bot booted. Will not fulfill subscriptions for {self.last_fulfill}:00 GMT or prior.')

    @commands.Cog.listener()
    async def on_ready(self):
        _logger.info(f'Bot is ready. Logged in as {self.bot.user.name}')
        _logger.info(f'Guilds: {", ".join([g.name for g in self.bot.guilds])}')
        _logger.info(f'Commands: {", ".join([c.name for c in self.bot.commands])}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        _logger.error(f'Error in {ctx.command}: {str(error)}')
    
    def _start_event_loop(self):
        # Start up the event loop
        self.last_fulfill = datetime.datetime.utcnow().hour
        self.fulfill_subscriptions.start()

    @staticmethod
    def _init_sql_commands():
        """Initialize database schema using the repository."""
        init_database_schema()

    def regenerate_all(self):
        """Regenerate all lectionaries using the registry."""
        registry.regenerate_all()

    @staticmethod
    def _index_lectionary_name(lectionary):
        """Get lectionary index from name using the registry."""
        return registry.get_index(lectionary)

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
                           '\"Greek Orthodox\" (shortcut `go`, currently disabled)\n'
                           '\"Russian Orthodox\" (shortcut `ro`)\n'
                           '\"Revised Common\" (shortcut `rcl` or `r`, currently disabled)\n'
                           )
            return

        index = self._index_lectionary_name(lec)

        if index > -1:
            lectionary = registry.get(index)
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

    @classmethod
    def _truncate_title(cls, title, max_length=256):
        if len(title) <= max_length:
            return title
        
        suffix = " ... [truncated]"
        suffix_length = len(suffix)
        truncated_length = max_length - suffix_length
        return f"{title[:truncated_length]}{suffix}"

    @classmethod
    async def send_lectionary(cls, ctx, lectionary):
        try:
            for piece in lectionary.build_json():
                if 'title' in piece and piece['title']:
                    piece['title'] = cls._truncate_title(piece['title'])
                await ctx.send(embed=discord.Embed.from_dict(piece))
        except Exception as e:
            error_msg = f"Error: please contact <@239877908435435520> for assistance\nDetails: {str(e)}"
            await ctx.send(error_msg)
            _logger.error(f"Error in send_lectionary: {str(e)}", exc_info=True)
    
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
        if time.isdigit():
            time = int(time)
        # If a meridiem was possibly specified
        else:
            time = time.lower()
            match = re.search(r'([0-9]+) *(am|pm)', time)
            if match:
                time = int(match.group(1))
                if match.group(2) == 'pm':
                    time += 12
            else:
                return None

        if not (self.EARLIEST_TIME <= time <= self.LATEST_TIME):
            return None

        return time

    @staticmethod
    def _update_guild_settings(guild_id, time):
        """Update or create guild settings using the repository."""
        GuildSettingsRepository.set_time(guild_id, time)

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
        """Ensure guild has settings entry using the repository."""
        GuildSettingsRepository.ensure_exists(guild_id, self.EARLIEST_TIME)

    async def _check_subscription_and_add(self, ctx, channel_id, sub_type, guild_id):
        """Check and add a subscription using the repository."""
        sub_name = registry.get_name(sub_type).title()
        
        # Check if already subscribed
        if SubscriptionsRepository.exists(channel_id, sub_type):
            await ctx.send(f'<#{channel_id}> is already subscribed to the {sub_name} lectionary.')
            return
        
        # Check subscription limit
        if SubscriptionsRepository.count_for_guild(guild_id) >= self.MAX_SUBSCRIPTIONS:
            await ctx.send(f'You can\'t have more than {self.MAX_SUBSCRIPTIONS} subscriptions per guild.')
            return
        
        # Add subscription
        SubscriptionsRepository.add(guild_id, channel_id, sub_type)
        await ctx.send(f'<#{channel_id}> has been subscribed to the {sub_name} lectionary.')

    @commands.command(aliases=['unsub'])
    @commands.has_permissions(manage_messages=True)
    async def unsubscribe(self, ctx, channel: discord.TextChannel = None, lectionary: str = None):
        """Unsubscribe from lectionaries using the repository."""
        if (channel is None) and (lectionary is None):
            # Remove all the guild's subscriptions (cascades via foreign key)
            GuildSettingsRepository.delete(ctx.guild.id)
            await ctx.send(f'All subscriptions for {ctx.guild.name} have been removed.')

        elif isinstance(channel, discord.TextChannel):
            channel_id = channel.id

            if lectionary is None:
                SubscriptionsRepository.delete_for_channel(channel_id)
                await ctx.send(f'<#{channel_id}> has been unsubscribed from all lectionaries.')
            else:
                sub_type = self._index_lectionary_name(lectionary)

                if sub_type == -1:
                    await ctx.send('You didn\'t specify a valid lectionary option.')
                    return

                SubscriptionsRepository.delete_for_channel(channel_id, sub_type)
                await ctx.send(
                    f'<#{channel_id}> has been unsubscribed from the {registry.get_name(sub_type).title()} lectionary.')

        else:
            await ctx.send('You didn\'t specify a valid unsubscription option.')

    def _build_subscriptions_list(self, ctx):
        """
        Helper method to generate an embed listing the subscriptions for a
        guild given the guild id.
        """
        time, subscriptions = self._get_subscriptions(ctx)
        embed = self._create_embed(ctx, time, subscriptions)
        return embed

    def _get_subscriptions(self, ctx):
        """Get subscriptions for a guild using the repository."""
        time = GuildSettingsRepository.get_time(ctx.guild.id)
        if time is None:
            time = self.EARLIEST_TIME
            GuildSettingsRepository.ensure_exists(ctx.guild.id, time)
        
        subscriptions = SubscriptionsRepository.get_for_guild(ctx.guild.id)
        return time, subscriptions

    def _create_embed(self, ctx, time, subscriptions):
        embed = discord.Embed(title=f'Subscriptions for {ctx.guild.name}')
        if subscriptions:
            embed.description = ''
            for subscription in subscriptions:
                channel_id = subscription[1]
                sub_name = registry.get_name(subscription[2]).title()
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
            _logger.debug('Shutdown request, logging out')
            await ctx.bot.close()
        except Exception as e:
            _logger.debug('An error occurred during shutdown: ' + str(e))
            await ctx.send(f'An error occurred during shutdown: {e}')

    @commands.command()
    @commands.is_owner()
    async def push(self, ctx, current_hour: int = datetime.datetime.utcnow().hour):
        _logger.debug(f'Manual subscription push requested for {current_hour}:00 GMT')

        try:
            if self.EARLIEST_TIME <= current_hour <= self.LATEST_TIME:
                # Regenerate all if it's the earliest time
                self.regenerate_all()

                await ctx.message.add_reaction('✅')
                await self.push_subscriptions(current_hour)
            else:
                await ctx.message.add_reaction('❌')
                _logger.debug(f'Push failed. current_hour={current_hour} is outside the acceptable range.')
        except Exception as e:
            _logger.debug(f'An error occurred during push: {e}')
            await ctx.send(f'An error occurred during push: {e}')

    '''SUBSCRIPTIONS TASK LOOP'''

    @tasks.loop(minutes=10)
    async def fulfill_subscriptions(self):
        # Push the current hour's subscriptions if they haven't been already
        current_hour = datetime.datetime.utcnow().hour

        if (self.EARLIEST_TIME <= current_hour <= self.LATEST_TIME) and (self.last_fulfill != current_hour):
            _logger.debug(f"Starting to fulfill subscriptions for {current_hour} hour")
            # Make sure the lectionary embeds are updated for the day
            self.regenerate_all()

            try:
                await self.push_subscriptions(current_hour)
                self.last_fulfill = current_hour
                _logger.debug(f"Successfully fulfilled subscriptions for {current_hour} hour")
            except Exception as e:
                _logger.debug(f"Error during fulfilling subscriptions for {current_hour} hour: {e}")

    @fulfill_subscriptions.before_loop
    async def before_fulfill_subscriptions(self):
        await self.bot.wait_until_ready()

    '''SUBSCRIPTIONS HELPER METHODS'''

    async def _remove_deleted_guilds(self):
        """
        Purge settings of deleted guilds using the repository.
        The ON CASCADE DELETE option also wipes subscriptions automatically.
        """
        guild_ids = GuildSettingsRepository.get_all_guild_ids()
        total = len(guild_ids)
        
        _logger.debug(f"Checking {total} guilds for deletion")
        
        deleted_guild_ids = [gid for gid in guild_ids if not self.bot.get_guild(gid)]
        
        if deleted_guild_ids:
            count = GuildSettingsRepository.delete_many(deleted_guild_ids)
            _logger.debug(f'Purged {count} out of {total} guilds')

    async def push_subscriptions(self, hour):
        """Push lectionary embeds to all channels subscribed for this hour."""
        await self._remove_deleted_guilds()
        
        subscriptions = SubscriptionsRepository.get_for_hour(hour)
        total_subs = len(subscriptions)
        successful_subs = 0

        if total_subs > 0:
            _logger.debug(f"Preparing to push {total_subs} subscription(s) for {hour}:00 GMT")

        # Each subscription is a tuple: (channel_id, sub_type)
        for channel_id, sub_type in subscriptions:
            channel = self.bot.get_channel(channel_id)

            if channel:
                lec = registry.get(sub_type)
                if lec:
                    feed = lec.build_json()
                    for item in feed:
                        await channel.send(embed=discord.Embed.from_dict(item))
                    successful_subs += 1
            else:
                # Channel was deleted, remove subscription
                SubscriptionsRepository.delete_by_channel_id(channel_id)

        if successful_subs > 0:
            _logger.debug(
                f'Successfully pushed {successful_subs} out of {total_subs} subscriptions for {hour}:00 GMT')


async def setup(bot):
    await bot.add_cog(LectionaryCog(bot))
