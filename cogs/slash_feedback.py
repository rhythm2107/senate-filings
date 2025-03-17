import discord
from discord.ext import commands
from discord import app_commands
import logging
from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_ui import FeedbackModal

class FeedbackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command: /feedback
    @app_commands.command(name="feedback", description="Send feedback via a pop-up form.")
    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    async def feedback_command(self, interaction: discord.Interaction):
        """Slash command that opens a feedback modal."""
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)

async def setup(bot: commands.Bot):
    """Load the FeedbackCog into the bot."""
    await bot.add_cog(FeedbackCog(bot))