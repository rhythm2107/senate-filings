import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from modules.config import (
    DISCORD_BOT_GUILD_ID,
    DISCORD_BOT_TOKEN,
    DISCORD_BOT_CMD_PREFIX,
    SUBSCRIBE_VIP_ROLE_ID,
    SUBSCRIBE_INFO_CHANNEL_ID
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=DISCORD_BOT_CMD_PREFIX, intents=intents)

async def load_extensions():
    await bot.load_extension("cogs.slash_senator")
    await bot.load_extension("cogs.slash_senatorlist")
    await bot.load_extension("cogs.slash_party")
    await bot.load_extension("cogs.slash_feedback")
    await bot.load_extension("cogs.slash_leaderboard")
    await bot.load_extension("cogs.slash_subscribe")

@bot.event
async def on_ready():
    guild = discord.Object(id=DISCORD_BOT_GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        print("Error syncing commands:", e)
    print("Bot is ready")

# Global error handler for app commands:
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    A global error handler for all app_commands (slash commands).
    """
    if isinstance(error, app_commands.CheckFailure):
        # For example, user doesn't have the required role
        msg = f"This is a <@&{SUBSCRIBE_VIP_ROLE_ID}> command. Consider subscribing here: <#{SUBSCRIBE_INFO_CHANNEL_ID}>",
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    else:
        # Log or handle other errors
        raise error


async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_BOT_TOKEN)

asyncio.run(main())