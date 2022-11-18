from helpers import bot_config
from helpers import logger

from discord.ext import commands
import discord

import os

config = bot_config.Config()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.prefix, intents=intents)
bot.remove_command('help')

for file in os.listdir('cogs'):
    if file.endswith('.py'):
        name = file[:-3]
        try:
            await bot.load_extension(f'cogs.{name}')
        except:
            print(name)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"{config.prefix}help"))
    print('Ready.')
    logger.log(f'Logged in as "{bot.user}"')

bot.run(config.token)