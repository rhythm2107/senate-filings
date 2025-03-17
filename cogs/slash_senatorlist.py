import discord
from discord.ext import commands
from discord import app_commands
import math

from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_db import get_senators
from bot_modules.bot_embed import create_embed_senator_list
from bot_modules.bot_ui import PaginatorView

class SenatorCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(
        name="senatorlist",
        description="List senators, with a custom sequential numbering across pages."
    )
    async def senatorlist(self, interaction: discord.Interaction):
        # Retrieve all senators, sorted by name
        senators = get_senators()
        if not senators:
            await interaction.response.send_message("No senators found in the database.")
            return

        per_page = 10
        total_pages = math.ceil(len(senators) / per_page)
        embeds = []

        # Build each page
        for page_index in range(total_pages):
            page_data = senators[page_index * per_page : (page_index + 1) * per_page]
            embed = create_embed_senator_list(
                page_index, total_pages, page_data, per_page
            )
            embeds.append(embed)

        # Use your PaginatorView
        view = PaginatorView(embeds, author_id=interaction.user.id)
        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(SenatorCommands(bot))
