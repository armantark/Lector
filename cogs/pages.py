import json

from discord import Embed
from discord.ext import commands


class Pages(commands.Cog):
    def __init__(self, bot):
        self.prefix = bot.command_prefix

        # Load the JSON data
        about_data = self.load_json('cogs/pages_data/about.json')
        commands_data = self.load_json('cogs/pages_data/commands.json')

        # Cache the info for building command-specific help pages
        self.command_help = commands_data['commands']
        self.command_redirects = commands_data['redirects']

        # Generate the about page and help page
        self.about_json = self.build_about_json(about_data)
        self.help_json = self.build_help_json(commands_data)

    @staticmethod
    def load_json(filename):
        with open(filename, encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def build_about_json(data):
        return {
            'title': data['title'],
            'description': data['description'],
            'fields': [
                {'name': name, 'value': value}
                for name, value in data['fields'].items()
            ]
        }

    def build_help_json(self, data):
        return {
            'title': data['title'],
            'description': data['description'].replace('<pre>', self.prefix) + '\n\n```\n' + '\n'.join(
                self.command_help) + '```'
        }

    def build_command_json(self, arg):
        # Given a command that is known to be in the command documentation,
        # generate an embed for it.
        return {
            'title': arg,
            'description': self.command_help[arg].replace('<base>', f'{self.prefix}{arg}')
        }

    @commands.command()
    async def about(self, ctx):
        await ctx.send(embed=Embed.from_dict(self.about_json))

    @commands.command(aliases=['h'])
    async def help(self, ctx, arg=None):
        if arg is None:
            data = self.help_json
        elif arg in self.command_help:
            data = self.build_command_json(arg)
        elif (arg in self.command_redirects) and (self.command_redirects[arg] in self.command_help):
            data = self.build_command_json(self.command_redirects[arg])
        else:
            data = {'color': 16711680, 'description': 'That command does not exist.'}

        await ctx.send(embed=Embed.from_dict(data))


async def setup(bot):
    await bot.add_cog(Pages(bot))
