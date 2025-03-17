import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from modules.config import DISCORD_BOT_GUILD_ID

GUILD_ID = DISCORD_BOT_GUILD_ID  # Replace with your real guild ID

def fetch_matching_senators(partial_name: str) -> list[str]:
    """Query the DB for up to 25 senator names that match partial_name."""
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    # e.g., assume you have a 'senators' table with senator_name
    # we use LIKE for partial matching, limit to 25
    c.execute("""
        SELECT canonical_full_name 
        FROM senators
        WHERE canonical_full_name LIKE ?
        ORDER BY canonical_full_name
        LIMIT 25
    """, (f"%{partial_name}%",))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_senator_info(name: str) -> str:
    """Fetch analytics for a senator by exact name."""
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("SELECT * FROM analytics WHERE senator_name = ?", (name,))
    row = c.fetchone()
    conn.close()
    if row:
        return f"Analytics for Senator {name}:\nTotal Transactions: {row[1]}"
    else:
        return f"No analytics data found for Senator {name}."

class AutocompleteInfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="info", description="Get senator analytics with name-based autocomplete")
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
        # Convert them to app_commands.Choice
        return [
            app_commands.Choice(name=name, value=name)
            for name in matches
        ]

async def setup(bot: commands.Bot):
    await bot.add_cog(AutocompleteInfoCog(bot))
