import random
import requests
import discord
import time
import asyncio
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
button2_off = discord.ui.Button(label='Deleted', style=discord.ButtonStyle.danger)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=908146735493296169))
    print('Ready!')


@tree.command(name='ping', description='Checks to see if the bot is online', guild=discord.Object(id=908146735493296169))
async def ping_command(interaction, user: discord.User):
    await interaction.response.send_message(f'Pong! {user.mention}')

@tree.command(name='flip', description='Flips a coin heads or tails', guild=discord.Object(id=908146735493296169))
async def flip_command(interaction):
    value = random.randrange(1,3)
    if value == 1:
        await interaction.response.send_message(f'Heads! You\'re a faggot!')
    else:    
        await interaction.response.send_message(f'Tails! You\'re a bitch ass nigga!')


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
    async with async_playwright() as p:
        await interaction.response.defer()
        
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

        # setup browser
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.roblox.com/signup')

        # set birthday
        await page.select_option('id=MonthDropdown', label='September')
        await page.select_option('id=DayDropdown', label='11')
        await page.select_option('id=YearDropdown', label='2001')

        # input username
        await page.fill('//*[@id="signup-username"]', str(username))
        await page.keyboard.press('Tab')

        # take screenshot
        await page.screenshot(path='screenshot.png')

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
        elif await page.get_by_text('Usernames may only contain letters, numbers, and _.', exact=True).is_visible():
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
        await interaction.followup.send(embed=embed, view=view)

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

        # close the browser to save ram
        await browser.close()

client.run('NjYxMDE5ODYwNDQ4NDQ0NDI2.GzV9zh.3Yhpqho_DduXVwtJjg-0LGHReLzeoA-_iKvf8A')
