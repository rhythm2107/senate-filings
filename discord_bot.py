import discord
from discord.ext import commands
import asyncio
from modules.config import (
    DISCORD_BOT_GUILD_ID,
    DISCORD_BOT_TOKEN,
    DISCORD_BOT_CMD_PREFIX
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=DISCORD_BOT_CMD_PREFIX, intents=intents)

async def load_extensions():
    await bot.load_extension("cogs.senator_commands")
    await bot.load_extension("cogs.ui_examples")
    await bot.load_extension("cogs.feedback_cog")
    await bot.load_extension("cogs.ex_info_cog")
    await bot.load_extension("cogs.partycog")

@bot.event
async def on_ready():
    guild = discord.Object(id=DISCORD_BOT_GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        print("Error syncing commands:", e)
    print("Bot is ready")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_BOT_TOKEN)

asyncio.run(main())