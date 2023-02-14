import discord
from discord.ext import commands
from pprint import pprint

from riotwatcher import LolWatcher, RiotWatcher


class Commands(commands.Cog):
    def __init__(self, bot, watcher):
        self.bot = bot
        self.region = "euw1"
        self.watcher: LolWatcher = watcher

    @commands.command(name="player")
    async def player(self, ctx: commands.Context, arg):
        await ctx.reply(self.watcher.summoner.by_name(self.region, arg))

    @commands.command(name="graph")
    async def graph(self, ctx: commands.Context, arg):
        # We retrieve the player
        player = self.watcher.summoner.by_name(self.region, arg)
        match_list = self.watcher.match.matchlist_by_puuid(self.region, player["puuid"])
        winrate = 0
        for match_id in match_list:
            match_detail = self.watcher.match.by_id(self.region, match_id)
            for participant in match_detail["info"]["participants"]:
                if participant["summonerId"] == player["id"]:
                    if participant["win"]:
                        winrate += 1
        pprint(winrate / len(match_list))


    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, arg):
        # We retrieve the player
        player = self.watcher.summoner.by_name(self.region, arg)
        # We get ranking informations
        tier: str = self.watcher.league.by_summoner(self.region, player["id"])[0]["tier"]
        rank: str = self.watcher.league.by_summoner(self.region, player["id"])[0]["rank"]
        await ctx.reply(tier.capitalize() + " " + rank)
