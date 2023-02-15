import sqlite3

import discord
from discord.ext import commands
from pprint import pprint

from riotwatcher import LolWatcher


class Commands(commands.Cog):
    def __init__(self, bot, watcher, connection, cursor):
        self.bot = bot
        self.region = "euw1"
        self.watcher: LolWatcher = watcher
        self.connection: sqlite3.Connection = connection
        self.cursor: sqlite3.Cursor = cursor

    def check_if_id_in_table(self, user_id):
        self.cursor.execute(f"SELECT EXISTS(SELECT TRUE FROM user_data WHERE user_id == {user_id});")
        return self.cursor.fetchone()[0]

    def check_if_summoner_in_table(self, summoner_name):
        self.cursor.execute(f"SELECT EXISTS(SELECT TRUE FROM user_data WHERE summoner == '{summoner_name}');")
        return self.cursor.fetchone()[0]

    @commands.command(name="test")
    async def test(self, ctx, summoner_name):
        player = self.watcher.summoner.by_name(self.region, summoner_name)
        match_list = self.watcher.match.matchlist_by_puuid(self.region, player["puuid"])
        pprint(self.watcher.match.by_id(self.region, match_list[0]))

    def winrate(self, summoner_name):
        # We retrieve the player
        player = self.watcher.summoner.by_name(self.region, summoner_name)
        match_list = self.watcher.match.matchlist_by_puuid(self.region, player["puuid"])
        win_rate = 0
        wins = 0
        loses = 0
        for match_id in match_list:
            match_detail = self.watcher.match.by_id(self.region, match_id)
            for participant in match_detail["info"]["participants"]:
                if participant["summonerId"] == player["id"]:
                    if participant["win"]:
                        win_rate += 1
                        wins += 1
                    else:
                        loses += 1
        win_rate = win_rate / len(match_list) * 100
        return win_rate, wins, loses

    @commands.command(name="addme")
    async def addme(self, ctx: commands.Context, player_name):
        sender_name = ctx.author.name
        sender_id = ctx.author.id

        if self.check_if_id_in_table(sender_id):
            await ctx.reply("Un utilisateur avec ce nom est déjà présent dans la base de données.")
        else:
            player_id = self.watcher.summoner.by_name(self.region, player_name)["id"]
            self.cursor.execute(f"INSERT INTO user_data VALUES ('{sender_name}', {sender_id}, '{player_name}', '{player_id}')")
            await ctx.reply("Vous avez bien été ajouté a la base de données")
        self.connection.commit()

    @commands.command(name="stats")
    async def stats(self, ctx: commands.Context, user: discord.Member = None):
        if not user:
            user = ctx.author
        if not self.check_if_id_in_table(user.id):
            await ctx.reply("La personne spécifiée n'est pas dans la base de données. "
                            "Si c'est vous, enregistrez-vous avec !addme <pseudo>")
        else:
            self.cursor.execute(f"SELECT summoner FROM user_data WHERE user_id == {user.id}")
            summoner_name = self.cursor.fetchone()[0]
            player = self.watcher.summoner.by_name(self.region, summoner_name)
            ranked_stats = self.watcher.league.by_summoner(self.region, player["id"])[0]
            queue_type: str = ranked_stats["queueType"]
            tier: str = ranked_stats["tier"]
            rank: str = ranked_stats["rank"]
            league_points = ranked_stats["leaguePoints"]
            win_rate, wins, loses = self.winrate(summoner_name)
            inactive = ranked_stats["inactive"]
            hot_streak = ranked_stats["hotStreak"]
            if inactive:
                inactive = "Oui"
            else:
                inactive = "Non"
            if hot_streak:
                hot_streak = "Oui"
            else:
                hot_streak = "Non"
            embed_stats = discord.Embed(title=f"Statistiques de {summoner_name}")
            embed_stats.add_field(name="Type de ranked", value=queue_type, inline=False)
            embed_stats.add_field(name="Rank", value=tier.capitalize() + f" {rank}", inline=False)
            embed_stats.add_field(name="LP", value=league_points, inline=False)
            embed_stats.add_field(name="Winrate, nombres de victoires, nombre de défaites",
                                  value=f"{win_rate}% de winrate, {wins} victoires, {loses} défaites.", inline=False)
            embed_stats.add_field(name="Inactif", value=inactive, inline=False)
            embed_stats.add_field(name="En winnerQ", value=hot_streak, inline=False)

            await ctx.send(embed=embed_stats)
