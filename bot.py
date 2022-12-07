import random
import requests
import discord
import time
from playwright.async_api import async_playwright
from discord import app_commands
from discord.ui import Button, View


# declare intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

button1 = discord.ui.Button(label='Save', style=discord.ButtonStyle.green)
button2 = discord.ui.Button(
    label='Screenshot', style=discord.ButtonStyle.blurple)
button3 = discord.ui.Button(
    label='Save', style=discord.ButtonStyle.green, disabled=True)
button4 = discord.ui.Button(
    label='Screenshot', style=discord.ButtonStyle.blurple, disabled=True)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=908146735493296169))
    print('Ready!')


@tree.command(name='ping', description='Checks to see if the bot is online', guild=discord.Object(id=908146735493296169))
async def ping(interaction, user: discord.User):
    await interaction.response.send_message(f'Pong! {user.mention}')

# @tree.command(name='gaydar', description='Checks how gay someone is by scanning all their sus messages', guild=discord.Object(id=908146735493296169))
# async def gaydar(interaction, user: discord.User):
#     counter = 0
#     async for message in interaction.channel.history(limit=1000):
#         if message.author == user:
#             if 'gay' in message.content:
#                 counter += 1
#     await interaction.response.send_message(f'has a score of {counter}/100')
    


@tree.command(name='capometer', description='With the latest discoveries by scientists at NASA, we can now detect if a statement is truly cap', guild=discord.Object(id=908146735493296169))
async def capometer(interaction, text: str):
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


@tree.command(name='check', description='Checks if a Roblox name is valid', guild=discord.Object(id=908146735493296169))
async def check(interaction, username: str):
    async with async_playwright() as p:
        # checkif username is already in file
        f = open('usernames.txt', 'r', encoding='utf-8')
        for line in f:
            if line.strip() == username:
                embed = discord.Embed(
                    title='Username Check', description=f'**{username}** is already in the list.', color=0xFF0000
                )
                await interaction.response.send_message(embed=embed)
                return

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
        time.sleep(.5)
        view = View()
        color = 0xFF0000
        if len(username) < 3 or len(username) > 20:
            await interaction.response.defer()
            description = f'**{username}** is too short/long.'

            view.add_item(button3)
            view.add_item(button4)
        elif await page.get_by_text('This username is already in use.', exact=True).is_visible():
            await interaction.response.defer()
            description = f'**{username}** is already in use.'

            view.add_item(button3)
            view.add_item(button4)
        elif await page.get_by_text('Username might contain private information.', exact=True).is_visible():
            await interaction.response.defer()
            description = f'**{username}** is flagged as containing private information.'

            view.add_item(button3)
            view.add_item(button4)
        elif await page.get_by_text('Username not appropriate for Roblox.', exact=True).is_visible():
            await interaction.response.defer()
            description = f'**{username}** is not appropriate.'

            view.add_item(button3)
            view.add_item(button4)
        else:
            await interaction.response.defer()
            description = f'**{username}** is available!'
            color = 0x00FF00

            view.add_item(button1)
            view.add_item(button4)

        # send the embed
        embed = discord.Embed(
            title='Username Check', description=description, color=color
        )
        await interaction.followup.send(embed=embed, view=view)
        
        # save button
        async def button1_callback(interaction):
            view.clear_items()
            view.add_item(button3)
            view.add_item(button4)
            await interaction.response.edit_message(view=view)
            f = open('usernames.txt', 'a')
            f.write(f'{username}\n')
            f.close()
        
        # screenshot button
        async def button2_callback(interaction):
            view.clear_items()
            view.add_item(button3)
            view.add_item(button4)
            embed.set_thumbnail(url='attachment://screenshot.png')
            await interaction.response.edit_message(content=discord.File('screenshot.png'), view=view)
        
        # define callbacks
        button1.callback = button1_callback
        button2.callback = button2_callback

        # close the browser to save ram
        await browser.close()

client.run('NjYxMDE5ODYwNDQ4NDQ0NDI2.GzV9zh.3Yhpqho_DduXVwtJjg-0LGHReLzeoA-_iKvf8A')
