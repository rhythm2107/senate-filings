import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_embed import build_analytics_embeds
from bot_modules.bot_ui import AnalyticsPaginatorView

############################
# Database / Data Retrieval
############################
def get_party_analytics(party_name: str):
    """
    Returns a row from analytics_party for the given party name,
    or None if not found. Each row is a 21-column tuple.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT 
            total_transaction_count,
            total_purchase_count,
            total_exchange_count,
            total_sale_count,
            total_stock_transactions,
            total_other_transactions,
            count_ownership_child,
            count_ownership_dependent_child,
            count_ownership_joint,
            count_ownership_self,
            count_ownership_spouse,
            total_transaction_value,
            average_transaction_amount,
            avg_perf_7d,
            avg_perf_30d,
            avg_perf_current,
            accuracy_7d,
            accuracy_30d,
            accuracy_current,
            total_net_profit,
            total_value
        FROM analytics_party
        WHERE party = ?
    """, (party_name,))
    row = c.fetchone()
    conn.close()
    return row  # None if not found, or a tuple with 21 columns

#####################
# The Cog
#####################
class PartyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(name="party", description="Show aggregated analytics for a political party.")
    @app_commands.describe(party="Pick a political party.")
    @app_commands.choices(
        party=[
            app_commands.Choice(name="Democratic Party", value="Democratic"),
            app_commands.Choice(name="Republican Party", value="Republican"),
        ]
    )
    async def party(self, interaction: discord.Interaction, party: str):
        """
        /party <Democratic|Republican>
        Returns a 4-page embed with relevant fields from analytics_party.
        """
        row = get_party_analytics(party)
        if not row:
            await interaction.response.send_message(f"No analytics data found for '{party}'.", ephemeral=True)
            return

        # Build 4 separate embed pages
        embeds = build_analytics_embeds(f"{party} Party", row)


        # Create the paginator
        view = AnalyticsPaginatorView(embeds, author_id=interaction.user.id)

        # Send the first page + attach the view
        await interaction.response.send_message(embed=embeds[0], view=view)
        # store the message so we can update it
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    """
    Standard setup function to load the PartyCog.
    """
    await bot.add_cog(PartyCog(bot))