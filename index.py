import asyncio
import logging
import os
import sys
import traceback

import discord
from discord.ext import commands

from helpers import bot_config
from helpers import logger

# Logging setup
logging.basicConfig(level=logging.INFO)

config = bot_config.Config()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents)
bot.remove_command('help')


# todo: Please add essential comments and docstrings to this code, nothing overexplaining code that is self-documenting.

async def main():
    for file in os.listdir('cogs'):
        if file.endswith('.py'):
            name = file[:-3]
            try:
                await bot.load_extension(f'cogs.{name}')
            except Exception as e:
                print(f'Failed to load extension {name}.', file=sys.stderr)
                traceback.print_exc()

    try:
        await bot.start(config.token)
    except Exception as e:
        logging.error(f"Error: {str(e)}")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"{config.prefix}help"))
    logging.info('Ready.')
    logger.log(f'Logged in as "{bot.user}"')


if __name__ == "__main__":
    asyncio.run(main())
