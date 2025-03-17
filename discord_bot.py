import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    await bot.load_extension("cogs.senator_commands")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

async def main():
    async with bot:
        await load_extensions()
        await bot.start("MTM1MDk1MTc0MTQzNjMyOTk5NQ.GPVw7R.reJhgtAHHl8lUw17Fiju_1dwQ6bdIAC4VF5yrE")

asyncio.run(main())