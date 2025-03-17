import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from modules.config import DISCORD_BOT_GUILD_ID

GUILD_ID = DISCORD_BOT_GUILD_ID  # Replace with your real guild ID

def fetch_matching_senators(partial_name: str) -> list[str]:
    """
    Query the DB for up to 25 senator names that match partial_name
    AND have a non-NULL total_value in analytics.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    # We do a JOIN to analytics to ensure the senator actually has a row there,
    # and we also filter a.total_value IS NOT NULL
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

def get_senator_info(name: str) -> str:
    """
    Fetch analytics for a senator by their exact canonical_full_name
    using a join on senators->analytics for all columns.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT a.senator_id,
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

    if not row:
        return f"No analytics data found for Senator {name}."

    (
        senator_id,
        total_tx,
        purchase_count,
        exchange_count,
        sale_count,
        stock_tx,
        other_tx,
        own_child,
        own_dep_child,
        own_joint,
        own_self,
        own_spouse,
        total_val,
        avg_val,
        perf_7d,
        perf_30d,
        perf_current,
        acc_7d,
        acc_30d,
        acc_current,
        net_profit,
        tot_value
    ) = row

    return (
        f"**Analytics for Senator {name} (ID: {senator_id})**\n"
        f"- **Total Transaction Count**: {total_tx}\n"
        f"- **Total Purchase Count**: {purchase_count}\n"
        f"- **Total Exchange Count**: {exchange_count}\n"
        f"- **Total Sale Count**: {sale_count}\n"
        f"- **Total Stock Transactions**: {stock_tx}\n"
        f"- **Total Other Transactions**: {other_tx}\n"
        f"- **Ownership (Child)**: {own_child}\n"
        f"- **Ownership (Dependent Child)**: {own_dep_child}\n"
        f"- **Ownership (Joint)**: {own_joint}\n"
        f"- **Ownership (Self)**: {own_self}\n"
        f"- **Ownership (Spouse)**: {own_spouse}\n"
        f"- **Total Transaction Value**: {total_val:,.2f}\n"
        f"- **Average Transaction Amount**: {avg_val:,.2f}\n"
        f"- **Avg Perf (7d)**: {perf_7d:.2f}%\n"
        f"- **Avg Perf (30d)**: {perf_30d:.2f}%\n"
        f"- **Avg Perf (Current)**: {perf_current:.2f}%\n"
        f"- **Accuracy (7d)**: {acc_7d:.2f}%\n"
        f"- **Accuracy (30d)**: {acc_30d:.2f}%\n"
        f"- **Accuracy (Current)**: {acc_current:.2f}%\n"
        f"- **Total Net Profit**: {net_profit:,.2f}\n"
        f"- **Total Value**: {tot_value:,.2f}"
    )

class AutocompleteInfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /senator command with senator_name autocomplete
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="senator", description="Get senator analytics with name-based autocomplete")
    @app_commands.describe(senator_name="The senator's name")
    async def info(self, interaction: discord.Interaction, senator_name: str):
        """Command that uses an autocomplete parameter for senator_name."""
        response = get_senator_info(senator_name)
        await interaction.response.send_message(response)

    @info.autocomplete("senator_name")
    async def senator_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Called as user types in the 'senator_name' param, returning up to 25 matches."""
        matches = fetch_matching_senators(current)
        return [
            app_commands.Choice(name=name, value=name)
            for name in matches
        ]

async def setup(bot: commands.Bot):
    await bot.add_cog(AutocompleteInfoCog(bot))