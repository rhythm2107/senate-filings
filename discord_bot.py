import discord
from discord.ext import commands
import sqlite3

# Define allowed guild IDs (replace with your actual server ID)
ALLOWED_GUILD_IDS = {1247226569869627582}  # example: {your_server_id}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=1247226569869627582)
        await bot.tree.sync(guild=guild)
        print(f"Synced commands for guild {guild.id}")
        print(f"Logged in as {bot.user}!")
    except Exception as e:
        print(f"An error occurred: {e}")

# Define a slash command
@bot.tree.command(name="info", description="Get analytics info for a senator by senator_id")
async def info(interaction: discord.Interaction, senator_id: int):
    # Check if the command is from an allowed guild
    if interaction.guild and interaction.guild.id not in ALLOWED_GUILD_IDS:
        await interaction.response.send_message("Sorry, this bot is not enabled in this server.", ephemeral=True)
        return

    # Connect to SQLite and fetch data (adjust as needed)
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("SELECT * FROM analytics WHERE senator_id = ?", (senator_id,))
    row = c.fetchone()
    conn.close()

    if row:
        # Format your response based on your table structure
        response = f"Analytics for Senator ID {senator_id}:\nTotal Transactions: {row[1]}"
    else:
        response = f"No analytics data found for Senator ID {senator_id}."
    
    await interaction.response.send_message(response)

@bot.tree.command(name="ping7", description="Check the bot's response time")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

if __name__ == "__main__":
    # Replace 'your_bot_token_here' with your actual Discord bot token.
    bot.run("MTM1MDk1MTc0MTQzNjMyOTk5NQ.GPVw7R.reJhgtAHHl8lUw17Fiju_1dwQ6bdIAC4VF5yrE")
