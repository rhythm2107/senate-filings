import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import math
from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_db import get_senators
from bot_modules.bot_embed import create_embed_senator_list
from bot_modules.bot_ui import PaginatorView

class SenatorCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command: /senatorlist
    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(name="senatorlist", description="List all senators with their ID and canonical full name")
    async def senatorlist(self, interaction: discord.Interaction):
        senators = get_senators()
        if not senators:
            await interaction.response.send_message("No senators found in the database.")
            return

        per_page = 10
        total_pages = math.ceil(len(senators) / per_page)
        embeds = []
        for i in range(total_pages):
            page_data = senators[i * per_page : (i + 1) * per_page]
            embed = create_embed_senator_list(i, total_pages, page_data)
            embeds.append(embed)

        view = PaginatorView(embeds, author_id=interaction.user.id)
        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()

    # Slash command: /info
    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(name="info", description="Get analytics info for a senator by senator_id")
    async def info(self, interaction: discord.Interaction, senator_id: int):
        conn = sqlite3.connect("filings.db")
        c = conn.cursor()
        c.execute("SELECT * FROM analytics WHERE senator_id = ?", (senator_id,))
        row = c.fetchone()
        conn.close()

        if row:
            response = f"Analytics for Senator ID {senator_id}:\nTotal Transactions: {row[1]}"
        else:
            response = f"No analytics data found for Senator ID {senator_id}."
        
        await interaction.response.send_message(response)

async def setup(bot: commands.Bot):
    await bot.add_cog(SenatorCommands(bot))
