import random
import requests
import discord
import time
import asyncio
import os
import redis
import math
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from discord.ui import Button, View
from discord.ext.commands import cooldown, BucketType
from dateutil.relativedelta import relativedelta as rd

load_dotenv()

# declare variables
bot = discord.Bot(intents=discord.Intents.default())
button1 = discord.ui.Button(label='Save', style=discord.ButtonStyle.primary)
button1_off = discord.ui.Button(
    label='Saved', style=discord.ButtonStyle.primary, disabled=True)
button2 = discord.ui.Button(label='Delete?', style=discord.ButtonStyle.danger)
button2_off = discord.ui.Button(
    label='Deleted', style=discord.ButtonStyle.danger, disabled=True)

FMT = '{0.minutes} minutes {0.seconds} seconds'
TESTING = True
TIPS = ['Use /shop to view items', 'Use /mine to mine for coins', 'Use /flip to gamble coins for chance', 'Use /gift to gift to a friend', 'You can mine every 15 minutes',
        'Use /wallet to check your wallet', 'You can check your ledger with /wallet', 'Upgrade your pickaxe with 200 coins', 'Check your inventory with /wallet']
REDIS = redis.Redis.from_url(
    url=str(os.getenv('REDIS_URL')),
    password=str(os.getenv('REDISPASSWORD'))
)


async def currency(user_id, change, currency_type=None):
    user_id = str(user_id)
    coins = REDIS.hget(user_id, 'coins')
    if coins == None:
        if change < 0:
            change = 0
        REDIS.hset(user_id, 'coins', value=str(change))
    else:
        REDIS.hset(user_id, 'coins',
                   value=str(int(coins)+int(change)))
        if currency_type is not None:
            if change > 0:
                change = f'+{change}'
            REDIS.lpush(f'{user_id}:ledger',
                        f'**{change}** _from_ **{currency_type}**')
            REDIS.ltrim(f'{user_id}:ledger', 0, 2)
    return int(REDIS.hget(user_id, 'coins'))


@bot.event
async def on_ready():
    global page
    if not TESTING:
        print('Creating browser...')
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.roblox.com/signup')
        await page.select_option('id=MonthDropdown', label='September')
        await page.select_option('id=DayDropdown', label='11')
        await page.select_option('id=YearDropdown', label='2001')
    print(f'{bot.user} is ready and online!')


@bot.slash_command(name='ping', description='Checks to see if the bot is online', guild=discord.Object(id=908146735493296169))
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        description=f'Bot latency is ``{latency}ms``', color=discord.Color.blue()
    )
    await ctx.respond(embed=embed)


@bot.slash_command(name='avatar', description='Get a user\'s avatar', guild=discord.Object(id=908146735493296169))
async def avatar(ctx, user: discord.Member = None):
    if user == None:
        user = ctx.user
    embed = discord.Embed(
        title=f'{user.name}\'s avatar', color=discord.Color.blue()
    )
    embed.set_image(url=user.avatar.with_size(1024))
    await ctx.respond(embed=embed)


@bot.slash_command(name='roulette', description='Play a game of roulette', guild=discord.Object(id=908146735493296169))
async def roulette(ctx, bet: int, type: str):
    await ctx.respond('Roulette is currently disabled!')
    return
    if await currency(ctx.user.id, 0) >= 50:
        if type == 'oddeven':
            view = View()
            odd = Button(label='Odd', style=discord.ButtonStyle.primary)
            even = Button(label='Even', style=discord.ButtonStyle.primary)

            view.add_item(odd)
            view.add_item(even)
            modal = discord.ui.Modal(
                title="Modal via Slash Command", value=ctx.children[0].value)
            await ctx.send_modal(modal)
            # await ctx.respond('Odd or Even?', view=view)

            # save button
            async def odd_callback(ctx):
                view.clear_items()
                modal = discord.ui.Modal(title="Modal via Slash Command")
                await ctx.send_modal(modal)
                # await ctx.response.edit_message(view=view, content='You chose odd!')

            async def even_callback(ctx):
                view.clear_items()
                await ctx.response.edit_message(view=view, content='You chose even!')

            # define callbacks
            odd.callback = odd_callback
            even.callback = even_callback
    else:
        await ctx.respond('You dont have enough coins!')


@bot.slash_command(name='gift', description='Gift a user coins!', guild=discord.Object(id=908146735493296169))
async def gift(ctx, user: discord.Member, coins: int):
    if coins < 0:
        description = 'You can\'t gift negative coins!'
    elif coins == 0:
        description = 'You can\'t gift nothing!'
    elif await currency(ctx.user.id, 0) < coins:
        description = 'You don\'t have enough coins!'
    else:
        await currency(ctx.user.id, -coins, 'gift')
        await currency(user.id, coins, 'gift')
        description = f'You gifted {user.mention} **{coins} coins**!'
    embed = discord.Embed(
        title='Gift', description=description, color=discord.Color.nitro_pink()
    )
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(embed=embed)


@bot.slash_command(name='flip', description='Flips a coin heads or tails bet on the winning side to win!', guild=discord.Object(id=908146735493296169))
async def flip(ctx, bet: int):
    if bet < 0:
        description = 'You can\'t bet negative coins!'
        color = discord.Color.red()
    elif await currency(ctx.user.id, 0) < bet:
        description = 'You don\'t have enough coins!'
        color = discord.Color.red()
    elif math.floor(int(await currency(ctx.user.id, 0))/2) < bet:
        description = 'You can\'t bet more than half of your coins!'
        color = discord.Color.red()
    elif bet > 10:
        description = 'You can\'t bet more than 10 coins!'
        color = discord.Color.red()
    else:
        if bool(random.getrandbits(1)):
            win = bet*2
            await currency(ctx.user.id, win, 'flip')
            description = f'You flipped a coin and you got **heads**. You won ** {win} coins**!'
            color = discord.Color.green()
        else:
            await currency(ctx.user.id, -bet, 'flip')
            description = f'You flipped a coin and you got **tails**. You lost ** {bet} coins**.'
            color = discord.Color.red()
    embed = discord.Embed(
        title='Coin Flip', description=description, color=color
    )
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(embed=embed)


@bot.slash_command(name='mine', description='Mine for coins', guild=discord.Object(id=908146735493296169))
@cooldown(1, 900, BucketType.user)
async def mine(ctx):
    # check if user has an upgraded pickaxe
    upgrade = bool(REDIS.hget(f'{ctx.user.id}', 'superpickaxe'))
    if upgrade:
        coins = random.randrange(10, 30)
        result = True
    else:
        coins = random.randrange(1, 10)
        if random.randint(1, 5) == 1:
            result = False
        else:
            result = True
            await currency(ctx.user.id, coins, 'mine')
    embed = discord.Embed(
        title='Mine', description='You mined with a **{}** and {}'.format('super pickaxe' if upgrade else 'normal pickaxe', f'found **{coins} coins**!' if result else 'found nothing.'), color=discord.Color.red() if not result else discord.Color.green()
    )
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(embed=embed)


@mine.error
async def info_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandOnCooldown):
        embed = discord.Embed(
            title='Cooldown', description=f'Try again in **{FMT.format(rd(seconds=round(error.retry_after)))}**', color=discord.Color.red()
        )
        embed.add_footer(text=random.choice(
            TIPS), icon_url=ctx.user.avatar.with_size(128))
        await ctx.respond(embed=embed)


@bot.slash_command(name='money', description='Dev command for adding money', guild=discord.Object(id=908146735493296169))
async def money(ctx, user: discord.Member, coins: int):
    if await bot.is_owner(ctx.user):
        await currency(user.id, coins, 'admin')
        if coins < 0:
            description = f'You took **{abs(coins)} coins** from {user.mention}!'
        else:
            description = f'You gave {user.mention} **{coins} coins**!'
    else:
        description = 'You don\'t have permission to use this command!'
    embed = discord.Embed(
        description=description, color=discord.Color.green(
        ) if bot.is_owner(ctx.user) else discord.Color.red()
    )
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name='wallet', description='Check the amount of coins you have', guild=discord.Object(id=908146735493296169))
async def wallet(ctx, hidden: bool = False):
    embed = discord.Embed(
        color=discord.Color.blue()
    )
    embed.add_field(name='Bank', value=f'You have **{await currency(ctx.user.id, 0)} coins**!', inline=False)
    embed.add_field(name='Inventory', value='**pickaxe**\n{}\n{}'.format('**superpickaxe**' if bool(REDIS.hget(f'{ctx.user.id}', 'superpickaxe'))
                    else 'superpickaxe', '**ultrapickaxe**' if bool(REDIS.hget(f'{ctx.user.id}', 'ultrapickaxe')) else 'ultrapickaxe'))

    # generate ledger
    ledger = REDIS.lrange(f'{ctx.user.id}:ledger', 0,
                          REDIS.llen(f'{ctx.user.id}:ledger'))
    if ledger is None or ledger == []:
        final = 'Empty'
    else:
        ledger = REDIS.lrange(f'{ctx.user.id}:ledger',
                              0, REDIS.llen(f'{ctx.user.id}:ledger'))
        final = ''
        for value in ledger:
            final += f'{value.decode("ascii")}\n'

    embed.add_field(name='Ledger', value=final)
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(embed=embed, ephemeral=True if hidden else False)


@bot.slash_command(name='capometer', description='With the latest discoveries by scientists at NASA, we can now detect if a statement is truly cap', guild=discord.Object(id=908146735493296169))
async def capometer(ctx, text: str):
    cap = random.randrange(0, 100)
    if cap > 75:
        description = f'"{text}" is **cap**.'
        color = discord.Color.red()
    elif cap > 50:
        description = f'"{text}" is **mixed**.'
        color = discord.Color.yellow()
    else:
        description = f'"{text}" is **hard fax**.'
        color = discord.Color.green()

    embedVar = discord.Embed(
        title='Cap-O-Meter', description=description, color=color
    )
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(embed=embedVar)


@bot.slash_command(name='usernames', description='List the usernames that have been saved by users with the check command', guild=discord.Object(id=908146735493296169))
async def usernames(ctx):
    usernames = REDIS.lrange('usernames', 0, REDIS.llen('usernames'))
    full = ''
    for user in usernames:
        full += f'{user.decode("ascii")}\n'
    embed = discord.Embed(
        title='Usernames', description=full, color=0x00FFFF
    )
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(embed=embed)


@bot.slash_command(name='shop', description='Buy items to use within the bot!', guild=discord.Object(id=908146735493296169))
async def shop(ctx, item: str = None):
    if item is None:
        embed = discord.Embed(
            title='Shop', description='You can buy items to use within the bot! Use `/shop <item>` to buy an item.', color=discord.Color.green()
        )
        embed.add_field(name='superpickaxe `200c`',
                        value='Upgrade the **yield** for mining and **prevents mining nothing**.', inline=False)
        embed.add_field(name='ultrapickaxe `1000c`',
                        value='Upgrade the **yield** to max.', inline=False)
        embed.add_footer(text=random.choice(
            TIPS), icon_url=ctx.user.avatar.with_size(128))
        await ctx.respond(embed=embed)
    else:
        if item.lower() == 'superpickaxe':
            print(REDIS.hget(f'{ctx.user.id}', 'superpickaxe'))
            if bool(REDIS.hget(f'{ctx.user.id}', 'superpickaxe')):
                embed = discord.Embed(
                    title='Shop', description='You already own this item!', color=discord.Color.red()
                )
            else:
                if await currency(ctx.user.id, 0) >= 200:
                    await currency(ctx.user.id, -200, 'pickaxe')
                    REDIS.hset(f'{ctx.user.id}', 'superpickaxe', 1)
                    embed = discord.Embed(
                        title='Shop', description='You bought a super pickaxe! Use `/mine` to mine for coins!', color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title='Shop', description='You don\'t have enough coins to buy this item!', color=discord.Color.red()
                    )
        elif item.lower() == 'ultrapickaxe':
            embed = discord.Embed(
                title='Shop', description='This item is out of stock!', color=discord.Color.red()
            )
            # if await currency(ctx.user.id, 0) >= 200:
            #     await currency(ctx.user.id, -800, 'ultrapickaxe')
            #     REDIS.hset(ctx.user.id, 'ultrapickaxe', 1)
            #     embed = discord.Embed(
            #         title='Shop', description='You bought a super pickaxe! Use `/mine` to mine for coins!', color=discord.Color.green()
            #     )
            # else:
            #     embed = discord.Embed(
            #         title='Shop', description='You don\'t have enough coins to buy this item!', color=discord.Color.red()
            #     )
        else:
            embed = discord.Embed(
                title='Shop', description='That item doesn\'t exist!', color=discord.Color.red()
            )
        embed.add_footer(text=random.choice(
            TIPS), icon_url=ctx.user.avatar.with_size(128))
        await ctx.respond(embed=embed)


@bot.slash_command(name='check', description='Checks if a Roblox name is valid, costs 1 coin to save', guild=discord.Object(id=908146735493296169))
async def check(ctx, username: str):
    await ctx.respond('The check command is currently disabled due to a bug. Please try again later.', ephemeral=True)
    return

    view = View()
    # check if username is already in database
    for entry in REDIS.lrange('usernames', 0, REDIS.llen('usernames')):
        if entry.decode('ascii') == username:
            embed = discord.Embed(
                title='Username Check', description=f'`{username}` is already in the list.', color=discord.Color.red()
            )
            view.add_item(button2)
            embed.add_footer(text=random.choice(
                TIPS), icon_url=ctx.user.avatar.with_size(128))
            await ctx.respond(embed=embed, view=view)

            async def button2_callback(ctx):
                view.clear_items()
                view.add_item(button2_off)
                index = 0
                for entry in REDIS.lrange('usernames', 0, REDIS.llen('usernames')):
                    if entry.decode('ascii') == username:
                        break
                    index += 1
                REDIS.lrem('usernames', index, username)
                await ctx.response.edit_message(view=view)

            # define callbacks
            button2.callback = button2_callback
            return

    # input username
    await page.fill('//*[@id="signup-username"]', str(username))
    await page.keyboard.press('Tab')

    # check username
    await asyncio.sleep(.5)
    if len(username) < 3 or len(username) > 20:
        description = f'`{username}` is too short/long.'

    elif await page.get_by_text('This username is already in use.', exact=True).is_visible():
        description = f'`{username}` is already in use.'

    elif await page.get_by_text('Username might contain private information.', exact=True).is_visible():
        description = f'`{username}` is flagged as containing private information.'

    elif await page.get_by_text('Username not appropriate for Roblox.', exact=True).is_visible():
        description = f'`{username}` is not appropriate.'

    # check if username contains any special characters
    elif any(char in username for char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '}', '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/', ' ']):
        description = f'`{username}` contains special characters.'

    else:
        description = f'`{username}` is available!'
        color = discord.Color.green()

        view.add_item(button1)

    # send the embed
    embed = discord.Embed(
        title='Username Check', description=description, color=discord.Color.red() if color is None else color
    )
    await page.screenshot(path='check.png')
    file = discord.File("check.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    embed.add_footer(text=random.choice(
        TIPS), icon_url=ctx.user.avatar.with_size(128))
    await ctx.respond(file=file, embed=embed, view=view)

    # save button
    async def button1_callback(ctx):
        if int(await currency(ctx.user.id, 0)) < 1:
            embed = discord.Embed(
                title='Username Check', description=f'`You don\'t have enough coins to save!', color=discord.Color.red()
            )
            embed.add_footer(text=random.choice(
                TIPS), icon_url=ctx.user.avatar.with_size(128))
            await ctx.respond(embed=embed)
        else:
            await currency(ctx.user.id, -1, 'save')
            view.clear_items()
            view.add_item(button1_off)
            REDIS.lpush('usernames', str(username))
            await ctx.response.edit_message(view=view)

    # define callbacks
    button1.callback = button1_callback


bot.run(str(os.getenv('TOKEN')))
