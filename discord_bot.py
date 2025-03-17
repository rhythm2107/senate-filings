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
    await bot.load_extension("cogs.slash_senator")
    await bot.load_extension("cogs.slash_senatorlist")
    await bot.load_extension("cogs.slash_party")
    await bot.load_extension("cogs.slash_feedback")
    await bot.load_extension("cogs.examples_ui")
    await bot.load_extension("cogs.slash_leaderboard")

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