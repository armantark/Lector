from lectionary.armenian          import ArmenianLectionary
from lectionary.bcp               import BookOfCommonPrayer
from lectionary.catholic          import CatholicLectionary
from lectionary.orthodox_american import OrthodoxAmericanLectionary
from lectionary.orthodox_coptic   import OrthodoxCopticLectionary
from lectionary.orthodox_greek    import OrthodoxGreekLectionary
from lectionary.orthodox_russian  import OrthodoxRussianLectionary
from lectionary.rcl               import RevisedCommonLectionary

from helpers.logger import log

import discord
from discord.ext import commands, tasks

import psycopg2
import typing
import re
import datetime
import os

# global DB connection, yo
# TODO: use a pool
conn = psycopg2.connect(os.environ['DATABASE_URL'])

class Lectionary(commands.Cog):
    MAX_SUBSCRIPTIONS = 10
    EARLIEST_TIME     = 7
    LATEST_TIME       = 23

    def __init__(self, bot):
        self.bot = bot

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

        log('Initial data fetch')

        # Initialize the database if it's not ready
        c    = conn.cursor()
        

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

        # Start up the event loop
        self.last_fufill = datetime.datetime.utcnow().hour
        self.fufill_subscriptions.start()

        log(f'Bot booted. Will not fufill subscriptions for {self.last_fufill}:00 GMT or prior.')

    
    def regenerate_all(self):
        for index in range(len(self.lectionaries)):
            self.lectionaries[index].regenerate()
        log('Refetched lectionary data')
    

    def _index_lectionary_name(self, lectionary):
        '''
        Given a lectionary name (str), returns its index number (int).
        If the name is invalid, -1 is returned.
        '''

        indexes = {
            'armenian':0,'a':0,
            'book of common prayer':1,'bcp':1,'b':1,
            'catholic':2,'c':2,
            'american orthodox':3,'orthodox american':3,'ao':3,'oa':3,
            'coptic orthodox':4,'co':4,
            'greek orthodox':5,'orthodox greek':5,'go':5,'og':5,
            'russian orthodox':6,'orthodox russian':6,'ro':6,'or':6,
            'revised common':7,'rcl':7,'r':7
        }

        if lectionary in indexes: return indexes[lectionary]
        else:                     return -1


    '''LECTIONARY REQUEST COMMAND'''

    @commands.command(aliases=['l'])
    async def lectionary(self, ctx, *lec):
        print(lec)
        if lec == None:
            await ctx.send('You didn\'t specify a lectionary.')
            return

        lec = ' '.join(lec).lower()
        index = self._index_lectionary_name(lec)

        if (index > -1):
            if not self.lectionaries[index].ready:
                self.lectionaries[index].regenerate()
                if not self.lectionaries[index].ready:
                    print('Lectionary not regenerated correctly.')
                    await ctx.message.add_reaction('❌')
                    return
            
            for piece in self.lectionaries[index].build_json():
                await ctx.send(embed=discord.Embed.from_dict(piece))
        else:
            await ctx.send('You didn\'t specify a valid lectionary.')
    

    '''SUBSCRIPTION COMMANDS'''

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def time(self, ctx, *, time=''):
        if (time == ''):
            now     = datetime.datetime.utcnow()
            output  = now.strftime(f'It is currently: %A, %B {now.day}, %Y, %I:%M:%S %p (GMT).')
            await ctx.send(output)
            return
        # If the user specified an integer, it's possibly 24-hour time
        elif time in re.findall(r'[0-9]+', time): time = int(time)
        # If a meridiem was possibly specified
        else:
            time = time.lower()
            match = re.search(r'([0-9]+) *(am|pm)', time)
            if match:
                time = int(match.group(1))
                if match.group(2) == 'pm': time += 12
            else:
                await ctx.send('You didn\'t specify a valid time.')
                return
        
        if not(self.EARLIEST_TIME <= time <= self.LATEST_TIME):
            await ctx.send(f'You need to specify a time from {self.EARLIEST_TIME} to {self.LATEST_TIME} GMT.')
            return

        guild_id = ctx.guild.id

        c    = conn.cursor()
        

        c.execute('SELECT * FROM GuildSettings WHERE guild_id = %s', (guild_id,))
        setting = c.fetchone()
        if setting:
            c.execute('UPDATE GuildSettings SET time = %s WHERE guild_id = %s', (time, guild_id))
        else:
            c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (guild_id, time))
        
        conn.commit()

        await ctx.send(f'The guild\'s subscriptions will come {time}:00 GMT daily.')


    @commands.command(aliases=['sub'])
    @commands.has_permissions(manage_messages=True)
    async def subscribe(self, ctx, lectionary=None, channel:typing.Optional[discord.TextChannel]=None):
        
        if lectionary is None:
            await ctx.send(embed=self._build_subcriptions_list(ctx))
            return
        
        sub_type = self._index_lectionary_name(lectionary)

        if sub_type == -1:
            await ctx.send('You didn\'t specify a valid lectionary option.')
            return
        
        c    = conn.cursor()
        

        if channel: channel_id = channel.id
        else:       channel_id = ctx.channel.id

        guild_id = ctx.guild.id

        # Check to see if the guild has a settings entry yet
        c.execute('SELECT * FROM GuildSettings WHERE guild_id = %s', (guild_id,))
        row = c.fetchone()
        if not row:
            # If not, create a default entry for the guild
            c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (guild_id, self.EARLIEST_TIME))

        # Check if the given channel is already subscribed to the given lectionary
        c.execute('SELECT * FROM Subscriptions WHERE channel_id=%s AND sub_type=%s', (channel_id, sub_type))
        row      = c.fetchone()
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


    @commands.command(aliases=['unsub'])
    @commands.has_permissions(manage_messages=True)
    async def unsubscribe(self, ctx, channel:discord.TextChannel=None, lectionary:str=None):
        c    = conn.cursor()
        

        if (channel is None) and (lectionary is None):
            # Remove all the guild's subscriptions
            c.execute('DELETE FROM GuildSettings WHERE guild_id = %s', (ctx.guild.id,))
            conn.commit()
            await ctx.send(f'All subscriptions for {ctx.guild.name} have been removed.')
        
        elif isinstance(channel, discord.TextChannel) and (lectionary is None):
            # Remove all subscriptions for the given channel
            channel_id = channel.id
            c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))
            conn.commit()
            await ctx.send(f'<#{channel_id}> has been unsubscribed from all lectionaries.')
        
        elif isinstance(channel, discord.TextChannel) and (lectionary is not None):
            # Remove specific subscriptions for the given channel
            channel_id = channel.id
            
            if lectionary is None:
                c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))
                conn.commit()
                await ctx.send(f'<#{channel_id}> has been unsubscribed from all lectionaries.')
                return

            sub_type = self._index_lectionary_name(lectionary)

            if sub_type == -1:
                conn.rollback()
                await ctx.send('You didn\'t specify a valid lectionary option.')
                return

            c.execute('DELETE FROM Subscriptions WHERE channel_id = %s AND sub_type = %s', (channel_id, sub_type))
            conn.commit()
            await ctx.send(f'<#{channel_id}> has been unsubscribed from the {self.lectionary_names[sub_type].title()} lectionary.')
        
        else:
            await ctx.send('You didn\'t specify a valid unsubscription option.')
    

    def _build_subcriptions_list(self, ctx):
        '''
        Helper method to generate an embed listing the subscriptions for a
        guild given the guild id.
        '''

        c    = conn.cursor()
        

        c.execute('SELECT time FROM GuildSettings WHERE guild_id = %s', (ctx.guild.id,))
        time = c.fetchone()
        if time:
            # This check is here to prevent a "Nonetype cannot be subscripted" error
            time = time[0]
        else:
            time = self.EARLIEST_TIME
            c.execute('INSERT INTO GuildSettings VALUES (%s, %s)', (ctx.guild.id, time))

        conn.commit()

        # Get all the subscription entries for the current guild
        c.execute('SELECT * FROM Subscriptions WHERE guild_id = %s', (ctx.guild.id,))
        subscriptions = c.fetchall()
        conn.commit()

        embed = discord.Embed(title=f'Subscriptions for {ctx.guild.name}')
        if subscriptions:
            embed.description = ''
            for subscription in subscriptions:
                channel_id      = subscription[1]
                sub_name        = self.lectionary_names[subscription[2]].title()
                embed.description += f'\n<#{channel_id}> - {sub_name} lectionary'

            embed.set_footer(text=f'(Daily @ {time}:00 GMT)')
        else:
            embed.description = 'There are none'
        
        return embed


    '''SYSTEM COMMANDS'''

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        '''
        Command to safely shutdown the bot with a reduced chance of
        damaging the database. (Bot owner only.)
        '''
        self.fufill_subscriptions.stop()
        await ctx.message.add_reaction('✅')
        log('Shutdown request, logging out')
        await ctx.bot.close()


    @commands.command()
    @commands.is_owner()
    async def push(self, ctx, current_hour:int=datetime.datetime.utcnow().hour):
        log(f'Manual subscription push requested for {current_hour}:00 GMT')

        if (self.EARLIEST_TIME <= current_hour <= self.LATEST_TIME):
            if (current_hour == self.EARLIEST_TIME): self.regenerate_all()
            await ctx.message.add_reaction('✅')
            await self.push_subscriptions(current_hour)
        else:
            await ctx.message.add_reaction('❌')
            log('Push failed.')


    '''SUBSCRIPTIONS TASK LOOP'''

    @tasks.loop(minutes=10)
    async def fufill_subscriptions(self):
        # Push the current hour's subscriptions if they haven't been already
        current_hour = datetime.datetime.utcnow().hour

        if (self.EARLIEST_TIME <= current_hour <= self.LATEST_TIME) and (self.last_fufill != current_hour):
            # Make sure the lectionary embeds are updated for the day
            if (current_hour == self.EARLIEST_TIME): self.regenerate_all()

            await self.push_subscriptions(current_hour)
            self.last_fufill = current_hour
    

    @fufill_subscriptions.before_loop
    async def before_fufill_subscriptions(self):
        await self.bot.wait_until_ready()
    

    '''SUBSCRIPTIONS HELPER METHODS'''

    async def _remove_deleted_guilds(self):
        '''
        Helper method to purge the settings of deleted guilds from
        the database. The ON CASCADE DELETE option in the database
        also makes this wipe the subscriptions automatically.
        '''
        c    = conn.cursor()
        

        c.execute('SELECT guild_id FROM GuildSettings')
        guild_ids = [item[0] for item in c.fetchall()]
        
        total = len(guild_ids)
        count = 0

        for guild_id in guild_ids:
            if not self.bot.get_guild(guild_id):
                c.execute('DELETE FROM GuildSettings WHERE guild_id = %s', (guild_id ,))
                count += 1
        
        conn.commit()

        if (count > 0): log(f'Purged {count} out of {total} guilds')
    

    async def push_subscriptions(self, hour):
        await self._remove_deleted_guilds()

        c    = conn.cursor()
        

        # Get all subscriptions for the guilds that have their time preference
        # set to the given hour
        c.execute('''
            SELECT Subscriptions.channel_id, Subscriptions.sub_type
            FROM Subscriptions
            INNER JOIN GuildSettings
            ON Subscriptions.guild_id = GuildSettings.guild_id
            WHERE GuildSettings.time = %s
        ''', (hour,))

        feeds = [
            self.lectionaries[index].build_json()
            for index in range(len(self.lectionaries))
        ]

        subscriptions = c.fetchall()
        # Each subscription is a tuple: (channel_id, sub_type)
        for subscription in subscriptions:
            channel_id = subscription[0]
            channel    = self.bot.get_channel(channel_id)
            sub_type   = subscription[1]

            if channel:
                for item in feeds[sub_type]:
                    await channel.send(embed=discord.Embed.from_dict(item))
            else:
                c.execute('DELETE FROM Subscriptions WHERE channel_id = %s', (channel_id,))
        
        conn.commit()

        if (len(subscriptions) > 0):
            log(f'Pushed {len(subscriptions)} subscription(s) for {hour}:00 GMT')
    

async def setup(bot):
    await bot.add_cog(Lectionary(bot))
