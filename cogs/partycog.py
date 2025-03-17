import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from modules.config import DISCORD_BOT_GUILD_ID

def get_party_analytics(party_name: str) -> str:
    """
    Fetch aggregated analytics from the 'analytics_party' table for the given party.
    Returns a nicely formatted string or a 'not found' message.
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

    if not row:
        return f"No analytics data found for '{party_name}'."

    # row now contains the columns in order:
    # (total_transaction_count, total_purchase_count, total_exchange_count, ... total_value)
    # Let's destructure them:
    (
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
    ) = row

    # Build a multiline string to display
    result = (
        f"**{party_name} - Aggregated Analytics**\n"
        f"• **Total Transaction Count**: {total_transaction_count}\n"
        f"• **Total Purchase Count**: {total_purchase_count}\n"
        f"• **Total Exchange Count**: {total_exchange_count}\n"
        f"• **Total Sale Count**: {total_sale_count}\n"
        f"• **Total Stock Transactions**: {total_stock_transactions}\n"
        f"• **Total Other Transactions**: {total_other_transactions}\n"
        f"• **Ownership (Child)**: {count_ownership_child}\n"
        f"• **Ownership (Dependent Child)**: {count_ownership_dependent_child}\n"
        f"• **Ownership (Joint)**: {count_ownership_joint}\n"
        f"• **Ownership (Self)**: {count_ownership_self}\n"
        f"• **Ownership (Spouse)**: {count_ownership_spouse}\n"
        f"• **Total Transaction Value**: {total_transaction_value}\n"
        f"• **Average Transaction Amount**: {average_transaction_amount}\n"
        f"• **Avg Perf (7d)**: {avg_perf_7d}\n"
        f"• **Avg Perf (30d)**: {avg_perf_30d}\n"
        f"• **Avg Perf (Current)**: {avg_perf_current}\n"
        f"• **Accuracy (7d)**: {accuracy_7d}\n"
        f"• **Accuracy (30d)**: {accuracy_30d}\n"
        f"• **Accuracy (Current)**: {accuracy_current}\n"
        f"• **Total Net Profit**: {total_net_profit}\n"
        f"• **Total Value**: {total_value}"
    )
    return result

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
        /party <Democratic Party|Republican Party>
        Fetches from analytics_party table using that party string.
        """
        result = get_party_analytics(party)
        await interaction.response.send_message(result)

async def setup(bot: commands.Bot):
    """
    Standard setup function to load the PartyCog.
    """
    await bot.add_cog(PartyCog(bot))
