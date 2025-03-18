import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_db import fetch_leaderboard
from bot_modules.bot_utilis import (
    get_leaderboard_choices,
    get_leaderboard_column_map,
    format_leaderboard_value,
    in_designated_channel
)

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @in_designated_channel()
    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(name="leaderboard", description="View top 10 senators by chosen criteria.")
    @app_commands.describe(criteria="Which leaderboard to display?")
    @app_commands.choices(criteria=get_leaderboard_choices())
    async def leaderboard_cmd(self, interaction: discord.Interaction, criteria: str):
        """
        /leaderboard <criteria>
        Renders a single embed with rank & name in bold + the numeric value.
        """
        # 1) Map user-friendly label (criteria) to actual DB column
        column_map = get_leaderboard_column_map()
        db_column = column_map[criteria]

        # 2) Fetch from DB
        rows = fetch_leaderboard(db_column)

        # 3) Build the embed
        embed = discord.Embed(title=f"{criteria} Leaderboard", color=discord.Color.blue())

        # If "Net Worth", add an extra note
        if criteria == "Net Worth":
            embed.description = "Approximate net worth based on aggregated data from analytics.\n(This includes spouse & dep. child if relevant.)"

        if not rows:
            embed.description = f"No senators found for the {criteria} leaderboard."
            await interaction.response.send_message(embed=embed)
            return

        # 4) Add fields for top 10
        for idx, (senator_name, val) in enumerate(rows, start=1):
            val_str = format_leaderboard_value(val, db_column)
            field_name = f"**{idx}) {senator_name}**"
            embed.add_field(name=field_name, value=val_str, inline=False)

        # 5) Send
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
