import discord
from discord.ext import commands
from discord import app_commands
import math

from modules.config import DISCORD_BOT_GUILD_ID, DISCORD_BOT_CMD_CHANNEL_ID
from bot_modules.bot_db import get_senators
from bot_modules.bot_embed import create_embed_senator_list
from bot_modules.bot_ui import PaginatorView
from bot_modules.bot_utilis import in_bot_commands_channel
from bot_modules.bot_exceptions import WrongChannelError

class SenatorCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @in_bot_commands_channel() # Check if the command is used in the designated channel
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

    @senatorlist.error
    async def senatorlist_cmd_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, WrongChannelError):
            message = (
                f"Basic bot commands must be used here: <#{DISCORD_BOT_CMD_CHANNEL_ID}>"
            )
        else:
            raise error  # Some other error we didn't handle

        # Now send the ephemeral message
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SenatorCommands(bot))
