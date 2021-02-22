from discord import Embed
from discord.ext import commands

import json
import datetime


class Pages(commands.Cog):
    def __init__(self, bot):
        self.prefix = bot.command_prefix

        # Generate the about page
        with open('cogs/pages_data/about.json', encoding='utf-8') as f:
            data = json.load(f)

        self.about_json = {
            'title':data['title'],
            'description':data['description'],
            'fields':[
                {
                    'name':name,
                    'value':value
                }
                for name, value in data['fields'].items()
            ]
        }

        # Generate the main help page and cahce the info for building command-
        # specific help pages
        with open('cogs/pages_data/commands.json', encoding='utf-8') as f:
            data = json.load(f)

        self.command_help      = data['commands']
        self.command_redirects = data['redirects']

        self.help_json = {
            'title':data['title'],
            'description':data['description'].replace('<pre>', self.prefix) + '\n\n```\n' + '\n'.join(self.command_help) + '```'
        }

    @commands.command()
    async def about(self, ctx):
        await ctx.send(embed=Embed.from_dict(self.about_json))


    @commands.command(aliases=['h'])
    async def help(self, ctx, arg=None):
        def build_command_json(arg):
            # Given a command that is known to be in the command documentation,
            # generate an embed for it.
            return {
                'title':arg,
                'description':self.command_help[arg].replace('<base>', f'{self.prefix}{arg}')
            }

        if arg is None:
            data = self.help_json
        elif arg in self.command_help:
            data = build_command_json(arg)
        elif (arg in self.command_redirects) and (self.command_redirects[arg] in self.command_help):
            data = build_command_json(self.command_redirects[arg])
        else:
            data = {'color':16711680,'description':'That command does not exist.'}
        
        await ctx.send(embed=Embed.from_dict(data))
        

def setup(bot):
    bot.add_cog(Pages(bot))