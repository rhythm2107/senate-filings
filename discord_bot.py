import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import math

ALLOWED_GUILD_IDS = {1247226569869627582}
GUILD = discord.Object(id=1247226569869627582)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def get_senators():
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("SELECT senator_id, canonical_full_name FROM senators ORDER BY senator_id")
    rows = c.fetchall()
    conn.close()
    return rows

def create_embed(page: int, pages: int, senators: list):
    embed = discord.Embed(
        title=f"Senators List (Page {page + 1}/{pages})",
        color=discord.Color.blue()
    )
    for senator_id, name in senators:
        embed.add_field(name=f"ID: {senator_id}", value=name, inline=False)
    return embed

class PaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author_id: int):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0
        self.message = None  # Will be set after sending the message
        self.author_id = author_id  # Store the original requester's ID

    async def update_message(self):
        if self.message:
            await self.message.edit(embed=self.embeds[self.current_page], view=self)

    def check_author(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_author(interaction):
            await interaction.response.send_message("You cannot control this pagination.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message()
            await interaction.response.defer()  # Acknowledge without sending a message
        else:
            await interaction.response.send_message("You're on the first page.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_author(interaction):
            await interaction.response.send_message("You cannot control this pagination.", ephemeral=True)
            return

        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_message()
            await interaction.response.defer()
        else:
            await interaction.response.send_message("You're on the last page.", ephemeral=True)


@bot.event
async def on_ready():
    for guild in bot.guilds:
        try:
            await bot.tree.sync(guild=guild)
            print(f"Synced commands for guild {guild.id}")
            cmds = bot.tree.get_commands(guild=guild)
            print("Commands in guild:", [cmd.name for cmd in cmds])
        except Exception as e:
            print(f"Error syncing commands for guild {guild.id}: {e}")
    print(f"Logged in as {bot.user}!")

@bot.tree.command(name="senatorlist", description="List all senators with their ID and canonical full name")
async def senatorlist(interaction: discord.Interaction):
    senators = get_senators()
    if not senators:
        await interaction.response.send_message("No senators found in the database.")
        return

    per_page = 10
    total_pages = math.ceil(len(senators) / per_page)
    embeds = []
    for i in range(total_pages):
        page_data = senators[i * per_page : (i + 1) * per_page]
        embed = create_embed(i, total_pages, page_data)
        embeds.append(embed)

    view = PaginatorView(embeds, author_id=interaction.user.id)
    await interaction.response.send_message(embed=embeds[0], view=view)
    view.message = await interaction.original_response()


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

if __name__ == "__main__":
    # Replace 'your_bot_token_here' with your actual Discord bot token.
    bot.run("MTM1MDk1MTc0MTQzNjMyOTk5NQ.GPVw7R.reJhgtAHHl8lUw17Fiju_1dwQ6bdIAC4VF5yrE")
