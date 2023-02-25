import datetime
import sqlite3
from pprint import pprint

import discord
from discord.ext import commands

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

    def winrate(self, wins, loses):
        win_rate = round(wins / (wins + loses) * 100)
        return win_rate

    @commands.command(name="addme")
    async def addme(self, ctx: commands.Context, player_name):
        sender_name = ctx.author.name
        sender_id = ctx.author.id

        if self.check_if_id_in_table(sender_id):
            await ctx.reply("Un utilisateur avec ce nom est déjà présent dans la base de données.")
        else:
            player_id = self.watcher.summoner.by_name(self.region, player_name)["id"]
            self.cursor.execute(
                f"INSERT INTO user_data VALUES ('{sender_name}', {sender_id}, '{player_name}', '{player_id}')")
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
            stats = self.get_stats(user)
            summoner_name = stats[0]
            queue_type = stats[1]
            tier: str = stats[2]
            rank: str = stats[3]
            league_points = stats[4]
            wins = stats[5]
            losses = stats[6]
            win_rate = stats[7]
            inactive = stats[8]
            hot_streak = stats[9]
            embed_stats = discord.Embed(title=f"Statistiques de {summoner_name}")
            embed_stats.add_field(name="Type de ranked", value=queue_type, inline=False)
            embed_stats.add_field(name="Rank", value=tier.capitalize() + f" {rank}", inline=False)
            embed_stats.add_field(name="LP", value=league_points, inline=False)
            embed_stats.add_field(name="Winrate, nombres de victoires, nombre de défaites",
                                  value=f"{win_rate}% de winrate, {wins} victoires, {losses} défaites.", inline=False)
            embed_stats.add_field(name="Inactif", value=inactive, inline=False)
            embed_stats.add_field(name="En winnerQ", value=hot_streak, inline=False)
            await ctx.send(embed=embed_stats)
            self.update_stats()

    def update_stats(self):
        self.cursor.execute(f"SELECT summoner_id FROM user_data")
        summoners = self.cursor.fetchall()[0]
        for summoner in summoners:
            summoner = self.watcher.summoner.by_id(self.region, summoner)
            stats = self.watcher.league.by_summoner(self.region, summoner["id"])[0]
            summoner_id = stats["summonerId"]
            tier: str = stats["tier"]
            rank: str = stats["rank"]
            league_points = stats["leaguePoints"]

            self.cursor.execute(f"SELECT date FROM player_data WHERE summoner_id == '{summoner_id}'")
            req = self.cursor.fetchall()
            now = datetime.datetime.now()
            if req:
                nearest_date = now - datetime.datetime.fromisoformat(req[0][0])
                for date in req[0]:
                    if now - datetime.datetime.fromisoformat(date) < nearest_date:
                        nearest_date = now - datetime.datetime.fromisoformat(date)
                matches = self.watcher.match.matchlist_by_puuid(self.region, summoner["puuid"])
                match_detail = self.watcher.match.by_id(self.region, matches[0])
                timestamp = match_detail["info"]["gameEndTimestamp"]
                print(timestamp)
                game_end_datetime = datetime.datetime.utcfromtimestamp(int(timestamp) / 1000)

    def get_stats(self, user: discord.Member):
        self.cursor.execute(f"SELECT summoner FROM user_data WHERE user_id == {user.id}")
        summoner_name = self.cursor.fetchone()[0]
        player = self.watcher.summoner.by_name(self.region, summoner_name)
        stats = self.watcher.league.by_summoner(self.region, player["id"])[0]
        queue_type: str = stats["queueType"]
        tier: str = stats["tier"]
        rank: str = stats["rank"]
        league_points = stats["leaguePoints"]
        wins = stats["wins"]
        losses = stats["losses"]
        win_rate = self.winrate(wins, losses)
        inactive = stats["inactive"]
        hot_streak = stats["hotStreak"]
        if inactive:
            inactive = "Oui"
        else:
            inactive = "Non"
        if hot_streak:
            hot_streak = "Oui"
        else:
            hot_streak = "Non"
        return summoner_name, queue_type, tier, rank, league_points, wins, losses, win_rate, inactive, hot_streak
