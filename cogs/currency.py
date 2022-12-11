import discord
import redis
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
REDIS = redis.Redis.from_url(
    url=str(os.getenv('REDIS_URL')),
    password=str(os.getenv('REDISPASSWORD'))
)


class Currency(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def currency(self, user_id, change):
        user_id = str(user_id)
        coins = REDIS.hget('coins', user_id)
        if coins == None:
            if change < 0:
                change = 0
            REDIS.hset('coins', user_id, value=str(change))
        else:
            REDIS.hset('coins', user_id,
                       value=str(int(coins)+int(change)))
        return REDIS.hget('coins', user_id)
    
    @commands.slash_command(name='gift', description='Gift a user coins!', guild=discord.Object(id=908146735493296169))
    async def gift(self, ctx, user: discord.Member, coins: int):
        economy = self.bot.get_cog('Currency')
        if coins < 0:
            description = 'You can\'t gift negative coins!'
        elif coins == 0:
            description = 'You can\'t gift nothing!'
        elif await economy.currency(ctx.user.id, 0) < coins:
            description = 'You don\'t have enough coins!'
        else:
            await economy.currency(ctx.user.id, -coins)
            await economy.currency(user.id, coins)
            description = f'You gifted {user.mention} {coins} coins!'
        embed = discord.Embed(
            title='Gift', description=description, color=0xFFFF00
        )
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(CogName(bot))
