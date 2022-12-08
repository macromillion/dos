import random
import requests
import discord
import time
import asyncio
import json
from playwright.async_api import async_playwright
from discord import app_commands
from discord.ui import Button, View


# declare intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

button1 = discord.ui.Button(label='Save', style=discord.ButtonStyle.primary)
button1_off = discord.ui.Button(
    label='Saved', style=discord.ButtonStyle.primary, disabled=True)
button2 = discord.ui.Button(label='Delete?', style=discord.ButtonStyle.danger)
button2_off = discord.ui.Button(
    label='Deleted', style=discord.ButtonStyle.danger)


async def get_coins(user_id, change):
    # open data file
    with open("data.json") as json_file:
        data = json.load(json_file)

    if change != 0:
        for user in data["users"]:
            if user["id"] == user_id:
                user["coins"] = user["coins"] + change

                # write to data file
                with open("data.json", "w") as outfile:
                    json.dump(data, outfile)

    # store user information
    result = False
    for user in data["users"]:
        if user["id"] == user_id:
            coins = user["coins"]
            result = True

    # if user does not exist, create them
    if not result:
        data["users"].append({
            "id": user_id,
            "coins": 0
        })

        # we already know coins is 0, no need to read file
        coins = 0

        # write to data file
        with open("data.json", "w") as outfile:
            json.dump(data, outfile)
    return coins


async def check_cooldown(user_id):
    # open data file
    with open("data.json") as json_file:
        data = json.load(json_file)

    # store user information
    result = False
    for user in data["users"]:
        if user["id"] == user_id:
            cooldown = user["cooldown"]
            result = True

    # if user does not exist, create them
    if not result:
        data["users"].append({
            "id": user_id,
            "coins": 0,
            "cooldown": ""
        })

        # we already know cooldown is empty, no need to read file
        cooldown = ""

        # write to data file
        with open("data.json", "w") as outfile:
            json.dump(data, outfile)
    return cooldown


@client.event
async def on_ready():
    global page
    await tree.sync(guild=discord.Object(id=908146735493296169))
    print('Creating browser...')
    # make the page variable global
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    await page.goto('https://www.roblox.com/signup')
    await page.select_option('id=MonthDropdown', label='September')
    await page.select_option('id=DayDropdown', label='11')
    await page.select_option('id=YearDropdown', label='2001')
    print('Ready!')


@tree.command(name='mine', description='Mine for coins', guild=discord.Object(id=908146735493296169))
async def mine_command(interaction):
    # get random true or false value
    value = random.randrange(1, 3)
    coins = random.randrange(1, 10)
    if value == 1:
        result = True
        await get_coins(interaction.user.id, coins)
    else:
        result = False
    embed = discord.Embed(
        title='Mine', description='You mined for coins and {}!'.format(f'found {coins} coins!' if result else 'found nothing.'), color=0xFF0000 if not result else 0x00FF00
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name='wallet', description='Check the amount of coins you have', guild=discord.Object(id=908146735493296169))
async def wallet_command(interaction):

    await interaction.response.send_message(f'You have {await get_coins(interaction.user.id, 0)} coins!')


@tree.command(name='ping', description='Checks to see if the bot is online', guild=discord.Object(id=908146735493296169))
async def ping_command(interaction, user: discord.User):
    await interaction.response.send_message(f'Pong! {user.mention}')


@tree.command(name='flip', description='Flips a coin heads or tails', guild=discord.Object(id=908146735493296169))
async def flip_command(interaction):
    value = random.randrange(1, 3)
    if value == 1:
        result = 'Heads!'
    else:
        result = 'Tails!'
    embed = discord.Embed(
        title='Coin Flip', description=result, color=0x00FFFF
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name='capometer', description='With the latest discoveries by scientists at NASA, we can now detect if a statement is truly cap', guild=discord.Object(id=908146735493296169))
async def capometer_command(interaction, text: str):
    cap = random.randrange(0, 100)
    if cap > 75:
        description = f'"{text}" is **cap**.'
        embedVar = discord.Embed(
            title='Cap-O-Meter', description=description, color=0xFF0000
        )
    elif cap > 50:
        description = f'"{text}" is **mixed**.'
        embedVar = discord.Embed(
            title='Cap-O-Meter', description=description, color=0xFFFF00
        )
    else:
        description = f'"{text}" is **hard fax**.'
        embedVar = discord.Embed(
            title='Cap-O-Meter', description=description, color=0x00FF00
        )

    await interaction.response.send_message(embed=embedVar)


@tree.command(name='list', description='List the usernames that have been saved by users with the check command', guild=discord.Object(id=908146735493296169))
async def list_command(interaction):
    f = open('usernames.txt', 'r', encoding='utf-8')
    usernames = ''
    for line in f:
        usernames += f'{line.strip()}\n'
    f.close()

    embed = discord.Embed(
        title='Username List', description=usernames, color=0x00FFFF
    )
    embed.set_footer(text='Check and add usernames with /check')

    await interaction.response.send_message(embed=embed)


@tree.command(name='check', description='Checks if a Roblox name is valid', guild=discord.Object(id=908146735493296169))
async def check_command(interaction, username: str):
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
            await interaction.followup.send(embed=embed, view=view)

            async def button2_callback(interaction):
                view.clear_items()
                view.add_item(button1_off)
                await interaction.response.edit_message(view=view)

            # define callbacks
            button2.callback = button2_callback
            return
    f.close()

    # input username
    await page.fill('//*[@id="signup-username"]', str(username))
    await page.keyboard.press('Tab')

    # check username
    await asyncio.sleep(1)
    if len(username) < 3 or len(username) > 20:
        description = f'`{username}` is too short/long.'

        view.add_item(button1_off)
    elif await page.get_by_text('This username is already in use.', exact=True).is_visible():
        description = f'`{username}` is already in use.'

        view.add_item(button1_off)
    elif await page.get_by_text('Username might contain private information.', exact=True).is_visible():
        description = f'`{username}` is flagged as containing private information.'

        view.add_item(button1_off)
    elif await page.get_by_text('Username not appropriate for Roblox.', exact=True).is_visible():
        description = f'`{username}` is not appropriate.'

        view.add_item(button1_off)
    # check if username contains any special characters
    elif any(char in username for char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '}', '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/']):
        description = f'`{username}` contains special characters.'

        view.add_item(button1_off)
    else:
        description = f'`{username}` is available!'
        color = 0x00FF00

        view.add_item(button1)

    # send the embed
    embed = discord.Embed(
        title='Username Check', description=description, color=color
    )
    await interaction.response.send_message(embed=embed, view=view)

    # save button
    async def button1_callback(interaction):
        view.clear_items()
        view.add_item(button1_off)
        await interaction.response.edit_message(view=view)
        f = open('usernames.txt', 'a')
        f.write(f'{username}\n')
        f.close()

    # define callbacks
    button1.callback = button1_callback


client.run('NjYxMDE5ODYwNDQ4NDQ0NDI2.GzV9zh.3Yhpqho_DduXVwtJjg-0LGHReLzeoA-_iKvf8A')
