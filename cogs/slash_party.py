import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID, SUBSCRIBE_VIP_ROLE_ID, DISCORD_VIP_CMD_CHANNEL_ID, SUBSCRIBE_INFO_CHANNEL_ID
from bot_modules.bot_exceptions import WrongChannelError, MissingVIPRoleError
from bot_modules.bot_embed import build_analytics_embeds
from bot_modules.bot_ui import AnalyticsPaginatorView
from bot_modules.bot_db import get_party_analytics
from bot_modules.bot_utilis import in_vip_commands_channel, has_required_role


class PartyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @in_vip_commands_channel()
    @app_commands.check(has_required_role)
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

    @party.error
    async def party_cmd_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """
        Distinguish which custom error was raised so we can send a specific message.
        """
        if isinstance(error, WrongChannelError):
            message = (
                f"This is a <@&{SUBSCRIBE_VIP_ROLE_ID}> command. You must use it here: <#{DISCORD_VIP_CMD_CHANNEL_ID}>"
            )
        elif isinstance(error, MissingVIPRoleError):
            message = (
                f"This is a <@&{SUBSCRIBE_VIP_ROLE_ID}> command. Consider subscribing here: <#{SUBSCRIBE_INFO_CHANNEL_ID}>"
            )
        else:
            raise error  # Some other error we didn't handle

        # Now send the ephemeral message
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

async def setup(bot: commands.Bot):
    """
    Standard setup function to load the PartyCog.
    """
    await bot.add_cog(PartyCog(bot))