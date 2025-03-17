import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

from modules.config import DISCORD_BOT_GUILD_ID

############################
# Database / Data Retrieval
############################
def get_party_analytics(party_name: str):
    """
    Returns a row from analytics_party for the given party name,
    or None if not found. Each row is a 21-column tuple.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT 
            total_transaction_count,
            total_purchase_count,
            total_exchange_count,
            total_sale_count,
            total_stock_transactions,
            total_other_transactions,
            count_ownership_child,
            count_ownership_dependent_child,
            count_ownership_joint,
            count_ownership_self,
            count_ownership_spouse,
            total_transaction_value,
            average_transaction_amount,
            avg_perf_7d,
            avg_perf_30d,
            avg_perf_current,
            accuracy_7d,
            accuracy_30d,
            accuracy_current,
            total_net_profit,
            total_value
        FROM analytics_party
        WHERE party = ?
    """, (party_name,))
    row = c.fetchone()
    conn.close()
    return row  # None if not found, or a tuple with 21 columns

#####################
# Build the Embeds
#####################
def build_party_embeds(party_name: str, row: tuple) -> list[discord.Embed]:
    """
    Build 4 separate pages (discord.Embed) for the user to page through.

    Page 1:
      - total_transaction_value
      - average_transaction_amount
      - total_net_profit
      - total_value

    Page 2 (Performance & Accuracy):
      - avg_perf_7d
      - avg_perf_30d
      - avg_perf_current
      - accuracy_7d
      - accuracy_30d
      - accuracy_current

    Page 3 (Transaction Counts):
      - transaction_count
      - purchase, sale, exchange
      - stock vs. other

    Page 4 (Ownership details):
      - self, spouse, joint, child, dep. child
    """

    # Destructure all columns
    (
        total_transaction_count,
        total_purchase_count,
        total_exchange_count,
        total_sale_count,
        total_stock_transactions,
        total_other_transactions,
        count_ownership_child,
        count_ownership_dependent_child,
        count_ownership_joint,
        count_ownership_self,
        count_ownership_spouse,
        total_transaction_value,
        average_transaction_amount,
        avg_perf_7d,
        avg_perf_30d,
        avg_perf_current,
        accuracy_7d,
        accuracy_30d,
        accuracy_current,
        total_net_profit,
        total_value
    ) = row

    # ---------- PAGE 1 ----------
    embed1 = discord.Embed(
        title=f"{party_name} Party Analytics (Page 1/4)",
        description="**Transaction Value & Net Profit**",
        color=discord.Color.blue()
    )
    embed1.add_field(
        name="Total Transaction Value",
        value=f"${int(total_transaction_value):,}",
        inline=False
    )
    embed1.add_field(
        name="Average Transaction Amount",
        value=f"${int(average_transaction_amount):,}",
        inline=False
    )
    embed1.add_field(
        name="Total Net Profit",
        value=f"${int(total_net_profit):,}",
        inline=False
    )
    embed1.add_field(
        name="Total Value",
        value=f"${int(total_value):,}",
        inline=False
    )

    # ---------- PAGE 2 ----------
    embed2 = discord.Embed(
        title=f"{party_name} Party Analytics (Page 2/4)",
        description="**Performance & Accuracy**",
        color=discord.Color.blue()
    )
    embed2.add_field(
        name="Avg Perf (7d)",
        value=f"{avg_perf_7d:.2f}%",
        inline=False
    )
    embed2.add_field(
        name="Avg Perf (30d)",
        value=f"{avg_perf_30d:.2f}%",
        inline=False
    )
    embed2.add_field(
        name="Avg Perf (Current)",
        value=f"{avg_perf_current:.2f}%",
        inline=False
    )
    embed2.add_field(
        name="Accuracy (7d)",
        value=f"{accuracy_7d:.2f}%",
        inline=False
    )
    embed2.add_field(
        name="Accuracy (30d)",
        value=f"{accuracy_30d:.2f}%",
        inline=False
    )
    embed2.add_field(
        name="Accuracy (Current)",
        value=f"{accuracy_current:.2f}%",
        inline=False
    )

    # ---------- PAGE 3 ----------
    embed3 = discord.Embed(
        title=f"{party_name} Party Analytics (Page 3/4)",
        description="**Transaction Counts**",
        color=discord.Color.blue()
    )
    # transaction counts
    embed3.add_field(
        name="Total Transaction Count",
        value=f"{total_transaction_count:,}",
        inline=False
    )
    embed3.add_field(
        name="Purchases",
        value=f"{total_purchase_count:,}",
        inline=False
    )
    embed3.add_field(
        name="Sales",
        value=f"{total_sale_count:,}",
        inline=False
    )
    embed3.add_field(
        name="Exchanges",
        value=f"{total_exchange_count:,}",
        inline=False
    )
    # transaction type
    embed3.add_field(
        name="Stock Transactions",
        value=f"{total_stock_transactions:,}",
        inline=False
    )
    embed3.add_field(
        name="Other Transactions",
        value=f"{total_other_transactions:,}",
        inline=False
    )

    # ---------- PAGE 4 ----------
    embed4 = discord.Embed(
        title=f"{party_name} Party Analytics (Page 4/4)",
        description="**Ownership**",
        color=discord.Color.blue()
    )
    embed4.add_field(
        name="Self",
        value=f"{count_ownership_self:,}",
        inline=False
    )
    embed4.add_field(
        name="Spouse",
        value=f"{count_ownership_spouse:,}",
        inline=False
    )
    embed4.add_field(
        name="Joint",
        value=f"{count_ownership_joint:,}",
        inline=False
    )
    embed4.add_field(
        name="Child",
        value=f"{count_ownership_child:,}",
        inline=False
    )
    embed4.add_field(
        name="Dep. Child",
        value=f"{count_ownership_dependent_child:,}",
        inline=False
    )

    return [embed1, embed2, embed3, embed4]

######################
# Paginator for 4 pages
######################
class PartyPaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author_id: int):
        super().__init__(timeout=180)  # 3 minutes or so
        self.embeds = embeds
        self.current_page = 0
        self.author_id = author_id
        self.message = None

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
            await interaction.response.defer()
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


#####################
# The Cog
#####################
class PartyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        embeds = build_party_embeds(party, row)

        # Create the paginator
        view = PartyPaginatorView(embeds, author_id=interaction.user.id)

        # Send the first page + attach the view
        await interaction.response.send_message(embed=embeds[0], view=view)
        # store the message so we can update it
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    """
    Standard setup function to load the PartyCog.
    """
    await bot.add_cog(PartyCog(bot))
