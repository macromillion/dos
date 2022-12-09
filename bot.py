import random
import requests
import discord
import time
import asyncio
import json
import os
from playwright.async_api import async_playwright
from discord.ui import Button, View
from discord.ext.commands import cooldown, BucketType
from dateutil.relativedelta import relativedelta as rd

# declare variables
bot = discord.Bot(intents=discord.Intents.default())
button1 = discord.ui.Button(label='Save', style=discord.ButtonStyle.primary)
button1_off = discord.ui.Button(
    label='Saved', style=discord.ButtonStyle.primary, disabled=True)
button2 = discord.ui.Button(label='Delete?', style=discord.ButtonStyle.danger)
button2_off = discord.ui.Button(
    label='Deleted', style=discord.ButtonStyle.danger)
fmt = '{0.minutes} minutes {0.seconds} seconds'

testing = True

async def get_coins(user_id, change):
    # load json
    with open("data.json") as json_file:
        data = json.load(json_file)
        
    # store user information
    result = False
    for user in data["users"]:
        if user["id"] == user_id:
            if "coins" in user:
                coins = user["coins"] = user["coins"] + change
                with open("data.json", "w") as outfile:
                    json.dump(data, outfile)
            else:
                # create coins key
                user["coins"] = coins = 0
                with open("data.json", "w") as outfile:
                    json.dump(data, outfile)
            result = True
    
    # create user if they do not exist
    if not result:
        data["users"].append({
            "id": user_id,
            "coins": 0,
            "cooldown": ""
        })
        coins = 0
        with open("data.json", "w") as outfile:
            json.dump(data, outfile)
        
    return coins

@bot.event
async def on_ready():
    global page
    if not testing:
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

@bot.slash_command(name='flip', description='Flips a coin heads or tails', guild=discord.Object(id=908146735493296169))
async def flip(ctx):
    if bool(random.getrandbits(1)):
        result = '**heads!**'
    else:
        result = '**tails!**'
    embed = discord.Embed(
        title='Coin Flip', description='You flipped a coin and you got ' + result, color=0x2F3136
    )
    await ctx.respond(embed=embed)

@bot.slash_command(name='mine', description='Mine for coins', guild=discord.Object(id=908146735493296169))
@cooldown(1, 3600, BucketType.user)
async def mine(ctx):
    coins = random.randrange(1, 10)
    if bool(random.getrandbits(1)):
        result = True
        await get_coins(ctx.user.id, coins)
    else:
        result = False
    embed = discord.Embed(
        title='Mine', description='You mined for coins and {}!'.format(f'found {coins} coins!' if result else 'found nothing.'), color=0xFF0000 if not result else 0x00FF00
    )
    await ctx.respond(embed=embed)

@mine.error
async def info_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandOnCooldown):
        embed = discord.Embed(
            title='Cooldown', description=f'Try again in **{fmt.format(rd(seconds=round(error.retry_after)))}**', color=0xFF0000
        )
        await ctx.respond(embed=embed)

@bot.slash_command(name='wallet', description='Check the amount of coins you have', guild=discord.Object(id=908146735493296169))
async def wallet(ctx):
    embed = discord.Embed(
        title='Wallet', description=f'You have {await get_coins(ctx.user.id, 0)} coins!', color=0x00FFFF
    )
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
    f = open('usernames.txt', 'r', encoding='utf-8')
    usernames = ""
    pages = []
    count = 0
    for line in f:
        if count == 10:
            count = 0
            pages.append(usernames)
            usernames = ""
        count += 1
        usernames += f'{line.strip()}\n'
    f.close()

    embed = discord.Embed(
        title='Username List', description=usernames, color=0x00FFFF
    )
    embed.set_footer(text='Page 1/{}'.format(len(pages) + 1))
    
    async def PageView():
        global page
        @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, disabled=True)
        async def back_callback(self, button, interaction):
            global page
            if page > 0:
                button.disabled = False
            page -= 1
        
        @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
        async def next_callback(self, button, interaction):
            global page
            if page == len(pages):
                button.disabled = True
            page += 1
            await interaction.response.send_message("Next!")

    await ctx.respond(embed=embed, view=PageView())


@bot.slash_command(name='check', description='Checks if a Roblox name is valid', guild=discord.Object(id=908146735493296169))
async def check(ctx, username: str):
    view = View()
    color = 0xFF0000

    # checkif username is already in file
    f = open('usernames.txt', 'r', encoding='utf-8')
    for line in f:
        if line.strip() == username:
            embed = discord.Embed(
                title='Username Check', description=f'`{username}` is already in the list.', color=color
            )
            view.add_item(button2)
            await ctx.respond(embed=embed, view=view)

            async def button2_callback(ctx):
                view.clear_items()
                view.add_item(button1_off)
                await ctx.response.edit_message(view=view)

            # define callbacks
            button2.callback = button2_callback
            return
    f.close()

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
    await ctx.respond(file=file, embed=embed, view=view)

    # save button
    async def button1_callback(ctx):
        view.clear_items()
        view.add_item(button1_off)
        await ctx.response.edit_message(view=view)
        f = open('usernames.txt', 'a')
        f.write(f'{username}\n')
        f.close()

    # define callbacks
    button1.callback = button1_callback


bot.run('NjQzMjAyOTU3MTc2NzMzNzQw.Gskb1P.-4eLOU7r0DVuGS-zwEvfGT2KSz3tPBa_TGUzbI')