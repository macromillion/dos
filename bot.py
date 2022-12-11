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
os.system('playwright install chromium')

# declare variables
bot = discord.Bot(intents=discord.Intents.default())
button1 = discord.ui.Button(label='Save', style=discord.ButtonStyle.primary)
button1_off = discord.ui.Button(
    label='Saved', style=discord.ButtonStyle.primary, disabled=True)
button2 = discord.ui.Button(label='Delete?', style=discord.ButtonStyle.danger)
button2_off = discord.ui.Button(
    label='Deleted', style=discord.ButtonStyle.danger, disabled=True)

FMT = '{0.minutes} minutes {0.seconds} seconds'
TESTING = False
REDIS = redis.Redis.from_url(
    url=str(os.getenv('REDIS_URL')),
    password=str(os.getenv('REDISPASSWORD'))
)


async def currency(user_id, change):
    user_id = str(user_id)
    coins = REDIS.hget('coins', user_id)
    if coins == None:
        if change < 0:
            change = 0
        REDIS.hset('coins', user_id, value=str(change))
    else:
        REDIS.hset('coins', user_id,
                   value=str(int(coins)+int(change)))
    return int(REDIS.hget('coins', user_id))

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
    await ctx.respond(f'Pong!')


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
        await currency(ctx.user.id, -coins)
        await currency(user.id, coins)
        description = f'You gifted {user.mention} {coins} coins!'
    embed = discord.Embed(
        title='Gift', description=description, color=0xFFFF00
    )
    await ctx.respond(embed=embed)


@bot.slash_command(name='flip', description='Flips a coin heads or tails bet on the winning side to win!', guild=discord.Object(id=908146735493296169))
async def flip(ctx, bet: int):
    if await currency(ctx.user.id, 0) < bet:
        description = 'You dont have enough coins!'
        color = 0xFF0000
    elif math.floor(int(await currency(ctx.user.id, 0))/2) < bet:
        description = 'You cant bet more than half of your coins!'
        color = 0xFF0000
    else:
        await currency(ctx.user.id, -bet)
        if bool(random.getrandbits(1)):
            win = bet*2
            await currency(ctx.user.id, win)
            description = f'You flipped a coin and you got **heads**. You won ** {win} coins**!'
            color = 0x00FF00
        else:
            description = f'You flipped a coin and you got **tails**. You lost ** {bet} coins**.'
            color = 0xFF0000
    embed = discord.Embed(
            title='Coin Flip', description=description, color=color
    )
    embed.set_footer(text='Spend you coins wisely!', icon_url=ctx.user.avatar)
    await ctx.respond(embed=embed)


@bot.slash_command(name='mine', description='Mine for coins', guild=discord.Object(id=908146735493296169))
@cooldown(1, 900, BucketType.user)
async def mine(ctx):
    coins = random.randrange(1, 10)
    if bool(random.getrandbits(1)):
        result = True
        await currency(ctx.user.id, coins)
    else:
        result = False
    embed = discord.Embed(
        title='Mine', description='You mined for coins and {}!'.format(f'found {coins} coins!' if result else 'found nothing.'), color=0xFF0000 if not result else 0x00FF00
    )
    embed.set_footer(text='You can mine again in 15 minutes!', icon_url=ctx.user.avatar)
    await ctx.respond(embed=embed)


@mine.error
async def info_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandOnCooldown):
        embed = discord.Embed(
            title='Cooldown', description=f'Try again in **{FMT.format(rd(seconds=round(error.retry_after)))}**', color=0xFF0000
        )
        await ctx.respond(embed=embed)


@bot.slash_command(name='money', description='Dev command for adding money', guild=discord.Object(id=908146735493296169))
async def money(ctx, user: discord.Member, coins: int):
    if ctx.user.id == 421129791920668672:
        await currency(user.id, coins)
        embed = discord.Embed(
            title='Money', description=f'You gave {user.mention} {coins} coins!', color=0x00FF00
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond('You are not allowed to use this command!')


@bot.slash_command(name='wallet', description='Check the amount of coins you have', guild=discord.Object(id=908146735493296169))
async def wallet(ctx, member: discord.Member = None):
    if member is None:
        coins = await currency(ctx.user.id, 0)
    else:
        coins = await currency(member.id, 0)
    embed = discord.Embed(
    title='Wallet' if member is None else f'{member.name}\'s Wallet', description=f'You have {await currency(ctx.user.id, 0)} coins!' if member is None else f'{member.name} has {await currency(member.id, 0)} coins!', color=0x00FFFF
    )
    embed.set_footer(text='Get more coins by mining, gambling, or being gifted!', icon_url=ctx.user.avatar)
    await ctx.respond(embed=embed)


@bot.slash_command(name='capometer', description='With the latest discoveries by scientists at NASA, we can now detect if a statement is truly cap', guild=discord.Object(id=908146735493296169))
async def capometer(ctx, text: str):
    cap = random.randrange(0, 100)
    if cap > 75:
        description = f'"{text}" is **cap**.'
        color = 0xFF0000
    elif cap > 50:
        description = f'"{text}" is **mixed**.'
        color = 0xFFFF00
    else:
        description = f'"{text}" is **hard fax**.'
        color = 0x00FF00

    embedVar = discord.Embed(
        title='Cap-O-Meter', description=description, color=color
    )
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
    await ctx.respond(embed=embed)


@bot.slash_command(name='check', description='Checks if a Roblox name is valid, costs 1 coin to save', guild=discord.Object(id=908146735493296169))
async def check(ctx, username: str):
    view = View()
    color = 0xFF0000

    # check if username is already in database
    for entry in REDIS.lrange('usernames', 0, REDIS.llen('usernames')):
        if entry.decode('ascii') == username:
            embed = discord.Embed(
                title='Username Check', description=f'`{username}` is already in the list.', color=0xFF0000
            )
            view.add_item(button2)
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
        color = 0x00FF00

        view.add_item(button1)

    # send the embed
    embed = discord.Embed(
        title='Username Check', description=description, color=color
    )
    await page.screenshot(path='check.png')
    file = discord.File("check.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text='Saving usernames costs 1 coin!', icon_url=ctx.user.avatar)
    await ctx.respond(file=file, embed=embed, view=view)

    # save button
    async def button1_callback(ctx):
        if int(await currency(ctx.user.id, 0)) < 1:
            embed = discord.Embed(
                    title='Username Check', description=f'`You don\'t have enough coins to save!', color=0xFF0000
            )
            embed.set_footer(text='You can get coins by mining, gambling, and more!')
            await ctx.respond(embed=embed)
        else:
            await currency(ctx.user.id, -1)
            view.clear_items()
            view.add_item(button1_off)
            REDIS.lpush('usernames', str(username))
            await ctx.response.edit_message(view=view)

    # define callbacks
    button1.callback = button1_callback


bot.run(str(os.getenv('TOKEN')))
