import discord
from discord.ext import commands

from riotwatcher import LolWatcher, RiotWatcher


class Commands(commands.Cog):
    def __init__(self, bot, watcher):
        self.bot = bot
        self.region = "euw1"
        self.watcher: LolWatcher = watcher

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, arg):
        player = self.watcher.summoner.by_name(self.region, arg)
        rank = self.watcher.league.by_summoner(self.region, player["id"])[0]["tier"]
        await ctx.reply(rank)
