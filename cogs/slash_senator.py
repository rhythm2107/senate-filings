import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID
# Import your universal embed builder & paginator
from bot_modules.bot_embed import build_analytics_embeds
from bot_modules.bot_ui import AnalyticsPaginatorView

GUILD_ID = DISCORD_BOT_GUILD_ID

def fetch_matching_senators(partial_name: str) -> list[str]:
    """
    Query the DB for up to 25 senator names that match partial_name
    and have a non-NULL total_value in analytics.
    (Adjust or remove the total_value IS NOT NULL filter if needed.)
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
    Return the same 21 columns as we do for 'analytics_party', in the same order,
    but for a single senator. If row not found, return None.
    The row must match the exact 21 columns to pass into build_analytics_embeds.
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

    return row  # None if not found, else 21 columns

class SenatorAnalyticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="senator", description="Get senator analytics with name-based autocomplete in a 4-page embed.")
    @app_commands.describe(senator_name="The senator's name")
    async def senator_cmd(self, interaction: discord.Interaction, senator_name: str):
        """
        /senator <name>
        If found, build 4-page analytics embed + paginator for that senator.
        """
        row = get_senator_analytics(senator_name)
        if not row:
            await interaction.response.send_message(f"No analytics data found for Senator '{senator_name}'.", ephemeral=True)
            return

        # Build the 4-page embed, passing e.g. "Senator John Smith" as the name
        embeds = build_analytics_embeds(f"Senator {senator_name}", row)
        view = AnalyticsPaginatorView(embeds, author_id=interaction.user.id)

        # Send first page
        await interaction.response.send_message(embed=embeds[0], view=view)
        # Store message reference for editing
        view.message = await interaction.original_response()

    # Autocomplete
    @senator_cmd.autocomplete("senator_name")
    async def senator_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Called as user types in the 'senator_name' param, returning up to 25 matches that have a non-NULL total_value.
        """
        matches = fetch_matching_senators(current)
        return [
            app_commands.Choice(name=name, value=name)
            for name in matches
        ]

async def setup(bot: commands.Bot):
    await bot.add_cog(SenatorAnalyticsCog(bot))