import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID

GUILD_ID = DISCORD_BOT_GUILD_ID

####################
# Helper Dictionary
####################
# Map the user-friendly choice to the actual analytics column name
leaderboard_columns = {
    "Total Volume": "total_transaction_value",       # 1
    "Total Transactions": "total_transaction_count", # 2
    "Average Transaction": "average_transaction_amount", # 3
    "Avg. % Growth 7 Days": "avg_perf_7d",           # 4
    "Avg. % Growth 30 Days": "avg_perf_30d",         # 5
    "Avg. % Growth Currently": "avg_perf_current",   # 6
    "Accuracy 7 Days": "accuracy_7d",               # 7
    "Accuracy 30 Days": "accuracy_30d",             # 8
    "Accuracy Currently": "accuracy_current",        # 9
    "Net Worth": "total_value",                     # 10
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
    Returns a list of tuples: (canonical_full_name, value).
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()

    # Build the WHERE clause if needed
    where_clause = "WHERE a.total_stock_transactions >= 15"
    params = []
    if column in stock_req_columns:
        # filter: total_stock_transactions >= 30
        where_clause = "WHERE a.total_stock_transactions >= 30"

    query = f"""
        SELECT s.canonical_full_name, a.{column}
          FROM analytics a
          JOIN senators s ON s.senator_id = a.senator_id
          {where_clause}
         ORDER BY a.{column} DESC
         LIMIT 10
    """

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    # rows: [(canonical_full_name, numeric_value), ...]
    return rows

def format_number(value: float, column: str) -> str:
    """
    Format the numeric value differently depending on the column:
    - If it's a percentage column (avg_perf or accuracy), add a '%' suffix.
    - Else, format with commas or .2f.
    """
    # Identify if it's a "perf" or "accuracy" column
    if column in {"avg_perf_7d", "avg_perf_30d", "avg_perf_current",
                  "accuracy_7d", "accuracy_30d", "accuracy_current"}:
        return f"{value:.2f}%"
    else:
        # For other numeric columns, let's just use a comma thousand separator + 2 decimal places
        return f"{value:,.2f}"

######################
# The Leaderboard Cog
######################
class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Define static choices
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
        Fetch top 10 from analytics (joined with senators) sorted descending by the chosen column.
        If criteria is one of the 'growth' or 'accuracy' ones, require total_stock_transactions >= 30.
        """
        # 1) Map the choice to the actual column
        column_name = leaderboard_columns[criteria]

        # 2) Query the DB for top 10
        rows = fetch_leaderboard(column_name)

        if not rows:
            await interaction.response.send_message(
                f"No senators found for the {criteria} leaderboard.",
                ephemeral=True
            )
            return

        # 3) Build a multiline string: "Rank. Name -> Value"
        lines = []
        for idx, (name, val) in enumerate(rows, start=1):
            # format the numeric value
            val_str = format_number(val, column_name)
            line = f"{idx}. {name} {val_str}"
            lines.append(line)

        # 4) Combine lines, send
        msg = f"**{criteria} Leaderboard**\n" + "\n".join(lines)
        await interaction.response.send_message(msg)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
