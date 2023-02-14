import discord
from discord.ext import commands

from riotwatcher import LolWatcher, ApiError

from bot_commands import Commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

with open("RIOT_TOKEN.txt", "r") as infile:
    RIOT_TOKEN = infile.read()

watcher = LolWatcher(RIOT_TOKEN)


@bot.event
async def on_ready():
    await bot.add_cog(Commands(bot, watcher))
    print("OK")


with open("TOKEN.txt", "r") as infile:
    TOKEN = infile.read()

bot.run(TOKEN)
