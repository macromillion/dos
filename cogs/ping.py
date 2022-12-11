import discord
from discord.ext import commands
from typing import Literal


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='ping', description='Checks the bot\'s latency and connectivity', guild=discord.Object(id=908146735493296169))
    async def ping(self, ctx, type: Literal['buy', 'sell']):
        if type == 'buy':
            await ctx.respond('You bought something!')
        elif type == 'sell':
            await ctx.respond('You sold something!')
        # latency = round(self.bot.latency * 1000)
        # embed = discord.Embed(
        #     title='Pong!', description=f'Bot Latency: {latency}ms', color=discord.Color.blue()
        # )
        # await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Ping(bot))
