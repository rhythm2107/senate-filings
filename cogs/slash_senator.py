import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID
from bot_modules.bot_embed import build_analytics_embeds  # universal 4-page embed builder
from bot_modules.bot_ui import AnalyticsPaginatorView     # universal paginator
from bot_modules.bot_db import get_senator_analytics, fetch_matching_senators
from bot_modules.bot_utilis import in_designated_channel, has_required_role

class SenatorAnalyticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.check(has_required_role)
    @in_designated_channel()
    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(name="senator", description="View 4-page analytics for a senator by name.")
    @app_commands.describe(senator_name="The senator's name")
    async def senator_cmd(self, interaction: discord.Interaction, senator_name: str):
        # fetch the row
        row = get_senator_analytics(senator_name)
        if not row:
            await interaction.response.send_message(f"No analytics data found for Senator '{senator_name}'.", ephemeral=True)
            return

        safe_row = tuple(x if x is not None else 0 for x in row)

        embeds = build_analytics_embeds(f"Senator {senator_name}", safe_row)
        view = AnalyticsPaginatorView(embeds, author_id=interaction.user.id)

        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()

    @senator_cmd.autocomplete("senator_name")
    async def senator_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        matches = fetch_matching_senators(current)
        return [
            app_commands.Choice(name=name, value=name)
            for name in matches
        ]

async def setup(bot: commands.Bot):
    await bot.add_cog(SenatorAnalyticsCog(bot))
