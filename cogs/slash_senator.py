import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_embed import build_analytics_embeds  # your universal 4-page embed builder
from bot_modules.bot_ui import AnalyticsPaginatorView     # your universal paginator

GUILD_ID = DISCORD_BOT_GUILD_ID

def fetch_matching_senators(partial_name: str) -> list[str]:
    """
    Query up to 25 senator names matching partial_name. We only filter out
    if total_value is NULL. (Or you can remove that filter entirely if you like.)
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT s.canonical_full_name
        FROM senators s
        JOIN analytics a ON a.senator_id = s.senator_id
        WHERE s.canonical_full_name LIKE ?
          AND a.total_value IS NOT NULL
        ORDER BY s.canonical_full_name
        LIMIT 25
    """, (f"%{partial_name}%",))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_senator_analytics(name: str):
    """
    Return the same 21 columns. If some are NULL, we won't block the entire row.
    We'll do row-based handling in the embed-building function.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT
            a.total_transaction_count,
            a.total_purchase_count,
            a.total_exchange_count,
            a.total_sale_count,
            a.total_stock_transactions,
            a.total_other_transactions,
            a.count_ownership_child,
            a.count_ownership_dependent_child,
            a.count_ownership_joint,
            a.count_ownership_self,
            a.count_ownership_spouse,
            a.total_transaction_value,
            a.average_transaction_amount,
            a.avg_perf_7d,
            a.avg_perf_30d,
            a.avg_perf_current,
            a.accuracy_7d,
            a.accuracy_30d,
            a.accuracy_current,
            a.total_net_profit,
            a.total_value
          FROM analytics AS a
          JOIN senators AS s ON s.senator_id = a.senator_id
         WHERE s.canonical_full_name = ?
    """, (name,))
    row = c.fetchone()
    conn.close()
    return row  # This can contain NULL in some columns.

class SenatorAnalyticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="senator", description="View 4-page analytics for a senator by name.")
    @app_commands.describe(senator_name="The senator's name")
    async def senator_cmd(self, interaction: discord.Interaction, senator_name: str):
        # fetch the row
        row = get_senator_analytics(senator_name)
        if not row:
            await interaction.response.send_message(f"No analytics data found for Senator '{senator_name}'.", ephemeral=True)
            return

        # build 4 pages, passing "Senator {name}" to the title
        # BUT we also must handle if some columns are NULL, so let's do that now:
        # We'll transform that row into a "safe" row that is guaranteed to be numeric or N/A placeholders.
        safe_row = tuple(x if x is not None else 0 for x in row)
        # or pass the row as-is if your universal builder function handles None. 
        # We'll see next how to handle it inside build_analytics_embeds.

        embeds = build_analytics_embeds(f"Senator {senator_name}", safe_row)
        view = AnalyticsPaginatorView(embeds, author_id=interaction.user.id)

        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()

    @senator_cmd.autocomplete("senator_name")
    async def senator_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        matches = fetch_matching_senators(current)
        return [
            app_commands.Choice(name=name, value=name)
            for name in matches
        ]

async def setup(bot: commands.Bot):
    await bot.add_cog(SenatorAnalyticsCog(bot))
