import sqlite3

import discord
from discord.ext import commands

from riotwatcher import LolWatcher, ApiError

from bot_commands import Commands


connection = sqlite3.connect("data.db")
cursor = connection.cursor()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

with open("RIOT_TOKEN.txt", "r") as infile:
    RIOT_TOKEN = infile.read()

watcher = LolWatcher(RIOT_TOKEN)


@bot.event
async def on_ready():
    await bot.add_cog(Commands(bot, watcher, connection, cursor))
    print("OK")


with open("TOKEN.txt", "r") as infile:
    TOKEN = infile.read()

bot.run(TOKEN)

connection.close()
