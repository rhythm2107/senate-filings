import discord
from discord.ext import commands
from discord import app_commands
import logging
from modules.config import (
    DISCORD_BOT_GUILD_ID,
    DISCORD_BOT_DEV_CHANNEL_ID
)

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

# ---------------------------------------------
# The Modal that pops up for the user to fill
# ---------------------------------------------
class FeedbackModal(discord.ui.Modal, title="User Feedback"):
    # Single text input field
    feedback = discord.ui.TextInput(
        label="Your Feedback",
        style=discord.TextStyle.long,
        placeholder="Describe your issue or suggestions...",
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Called when user submits the modal."""
        # 1) Log to a file (assuming Python's logging is configured)
        user_tag = f"{interaction.user} (ID: {interaction.user.id})"
        logging.info(f"Feedback from {user_tag}: {self.feedback.value}")

        # 2) Send to a private dev channel
        dev_channel = interaction.client.get_channel(DISCORD_BOT_DEV_CHANNEL_ID)
        if dev_channel:
            await dev_channel.send(
                content=(
                    f"**New Feedback**\n"
                    f"From: {user_tag}\n"
                    f"Content:\n{self.feedback.value}"
                )
            )

        # 3) Acknowledge the user with an ephemeral message
        await interaction.response.send_message(
            "Thank you! Your feedback has been received.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    """Load the FeedbackCog into the bot."""
    await bot.add_cog(FeedbackCog(bot))
