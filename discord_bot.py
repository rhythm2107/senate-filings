import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# Replace with your actual guild ID
ALLOWED_GUILD_IDS = {1247226569869627582}
GUILD = discord.Object(id=1247226569869627582)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Define your slash commands normally
@bot.tree.command(name="info", description="Get analytics info for a senator by senator_id")
async def info(interaction: discord.Interaction, senator_id: int):
    if interaction.guild and interaction.guild.id not in ALLOWED_GUILD_IDS:
        await interaction.response.send_message("This bot is not enabled in this server.", ephemeral=True)
        return

    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("SELECT * FROM analytics WHERE senator_id = ?", (senator_id,))
    row = c.fetchone()
    conn.close()

    if row:
        response = f"Analytics for Senator ID {senator_id}:\nTotal Transactions: {row[1]}"
    else:
        response = f"No analytics data found for Senator ID {senator_id}."
    
    await interaction.response.send_message(response)

@bot.tree.command(name="ping", description="Check the bot's response time")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="senatorlist", description="List all senators with their ID and canonical full name")
async def senatorlist(interaction: discord.Interaction):
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("SELECT senator_id, canonical_full_name FROM senators")
    rows = c.fetchall()
    conn.close()

    if not rows:
        response = "No senators found in the database."
    else:
        response = "\n".join(f"{row[0]}: {row[1]}" for row in rows)
    
    await interaction.response.send_message(response)

@bot.event
async def on_ready():
    # Clear guild-specific commands for our test guild
    try:
        bot.tree.clear_commands(guild=GUILD)
        print("Cleared commands for guild", GUILD.id)
    except Exception as e:
        print("Error clearing commands:", e)
    
    # Explicitly add our commands to the tree for our guild
    bot.tree.add_command(info, guild=GUILD)
    bot.tree.add_command(ping, guild=GUILD)
    bot.tree.add_command(senatorlist, guild=GUILD)
    
    # Now sync for that guild
    try:
        synced = await bot.tree.sync(guild=GUILD)
        print(f"Synced {len(synced)} commands for guild {GUILD.id}")
        cmds = bot.tree.get_commands(guild=GUILD)
        print("Commands in guild:", [cmd.name for cmd in cmds])
    except Exception as e:
        print("Error syncing commands:", e)
    
    print(f"Logged in as {bot.user}!")

if __name__ == "__main__":
    # Replace 'your_bot_token_here' with your actual Discord bot token.
    bot.run("MTM1MDk1MTc0MTQzNjMyOTk5NQ.GPVw7R.reJhgtAHHl8lUw17Fiju_1dwQ6bdIAC4VF5yrE")
