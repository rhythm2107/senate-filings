import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID

GUILD_ID = DISCORD_BOT_GUILD_ID

####################
# Mapping Columns
####################
leaderboard_columns = {
    "Total Volume": "total_transaction_value",
    "Total Transactions": "total_transaction_count",
    "Average Transaction": "average_transaction_amount",
    "Avg. % Growth 7 Days": "avg_perf_7d",
    "Avg. % Growth 30 Days": "avg_perf_30d",
    "Avg. % Growth Currently": "avg_perf_current",
    "Accuracy 7 Days": "accuracy_7d",
    "Accuracy 30 Days": "accuracy_30d",
    "Accuracy Currently": "accuracy_current",
    "Net Worth": "total_value",
}

# Columns that require total_stock_transactions >= 30
stock_req_columns = {
    "avg_perf_7d", "avg_perf_30d", "avg_perf_current",
    "accuracy_7d", "accuracy_30d", "accuracy_current"
}

def fetch_leaderboard(column: str) -> list[tuple[str, float]]:
    """
    Fetch top 10 from analytics, joined with senators, sorted descending by the given column.
    If column is in stock_req_columns, require total_stock_transactions >= 30.
    Returns a list of (canonical_full_name, numeric_value).
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()

    where_clause = ""
    if column in stock_req_columns:
        where_clause = "WHERE a.total_stock_transactions >= 30"

    query = f"""
        SELECT s.canonical_full_name, a.{column}
          FROM analytics a
          JOIN senators s ON s.senator_id = a.senator_id
          {where_clause}
         ORDER BY a.{column} DESC
         LIMIT 10
    """
    c.execute(query)
    rows = c.fetchall()
    conn.close()

    return rows  # e.g. [("John Doe", 12345.67), ...]

def format_number(value: float, column: str) -> str:
    """
    Format the numeric value based on the chosen column:
     - If it's a perf/accuracy column, do xx.xx%.
     - If it's total_transaction_count, do integer with commas (e.g. 12,345).
     - If it's total_transaction_value / average_transaction_amount / total_value => integer with commas plus '$'.
     - Otherwise, fallback to .2f with comma separators.
    """
    # Perf or accuracy
    if column in stock_req_columns:
        return f"{value:.2f}%"
    
    # total_transaction_count: int with commas
    if column == "total_transaction_count":
        return f"{int(value):,}"

    # net worth, total volume, average transaction => integer + commas + $
    if column in {"total_value", "total_transaction_value", "average_transaction_amount"}:
        return f"${int(value):,}"
    
    # fallback => .2f with commas
    return f"{value:,.2f}"

def build_leaderboard_embed(criteria: str, column: str) -> discord.Embed:
    """
    Two-line style for each rank:
    - Field name: "**1) John Doe**"
    - Field value: numeric value
    - If criteria == "Net Worth" we add a note in the embed description.
    """
    rows = fetch_leaderboard(column)
    embed = discord.Embed(
        title=f"{criteria} Leaderboard",
        color=discord.Color.blue()
    )

    # Special note for Net Worth
    if criteria == "Net Worth":
        embed.description = "Approximate net worth based on aggregated data from analytics.\nMeasures only stock holdings, includes Spouse and Dependent accounts."

    if not rows:
        embed.description = f"No senators found for the {criteria} leaderboard."
        return embed

    for idx, (name, val) in enumerate(rows, start=1):
        val_str = format_number(val, column)
        field_name = f"**{idx}) {name}**"
        field_value = val_str
        embed.add_field(name=field_name, value=field_value, inline=False)

    return embed

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # We define static choices for the command param
    leaderboard_choices = [
        app_commands.Choice(name="Total Volume", value="Total Volume"),
        app_commands.Choice(name="Total Transactions", value="Total Transactions"),
        app_commands.Choice(name="Average Transaction", value="Average Transaction"),
        app_commands.Choice(name="Avg. % Growth 7 Days", value="Avg. % Growth 7 Days"),
        app_commands.Choice(name="Avg. % Growth 30 Days", value="Avg. % Growth 30 Days"),
        app_commands.Choice(name="Avg. % Growth Currently", value="Avg. % Growth Currently"),
        app_commands.Choice(name="Accuracy 7 Days", value="Accuracy 7 Days"),
        app_commands.Choice(name="Accuracy 30 Days", value="Accuracy 30 Days"),
        app_commands.Choice(name="Accuracy Currently", value="Accuracy Currently"),
        app_commands.Choice(name="Net Worth", value="Net Worth"),
    ]

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="leaderboard", description="View top 10 senators by chosen criteria.")
    @app_commands.describe(criteria="Which leaderboard to display?")
    @app_commands.choices(criteria=leaderboard_choices)
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        criteria: str
    ):
        """
        /leaderboard <criteria>
        Renders a two-line embed approach with rank & name in bold, numeric on second line,
        with advanced formatting depending on column type.
        """
        column_name = leaderboard_columns[criteria]
        embed = build_leaderboard_embed(criteria, column_name)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
