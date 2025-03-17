import discord
import math

def create_embed_senator_list(
    page_index: int,
    total_pages: int,
    page_data: list[tuple[int, str, str, str]],
    per_page: int
) -> discord.Embed:
    """
    page_data is the slice of senator rows for this page, each (senator_id, full_name, state, party).
    We ignore 'senator_id' for numbering, using (page_index, per_page, local_index).
    """
    embed = discord.Embed(
        title=f"Senators List (Page {page_index + 1}/{total_pages})",
        color=discord.Color.blue()
    )

    # The global starting index for this page
    start_idx = page_index * per_page

    for local_i, (sen_id, full_name, state, party) in enumerate(page_data):
        # Compute a "global" number: first page is 1..10, second is 11..20, etc.
        global_number = start_idx + local_i + 1

        # Bold line: "XX. Full Name"
        field_name = f"**{global_number}. {full_name}**"
        # Second line: "Party - State"
        field_value = f"{party or 'N/A'} - {state or 'N/A'}"

        embed.add_field(name=field_name, value=field_value, inline=False)

    return embed


def build_analytics_embeds(name: str, row: tuple) -> list[discord.Embed]:
    """
    Build 4 pages of analytics based on a 21-column row from analytics or analytics_party.

    :param name: The label to show in the embed title (e.g. "Democratic Party", or "Senator John Doe").
    :param row: A tuple of 21 columns in this order:
      1  total_transaction_count
      2  total_purchase_count
      3  total_exchange_count
      4  total_sale_count
      5  total_stock_transactions
      6  total_other_transactions
      7  count_ownership_child
      8  count_ownership_dependent_child
      9  count_ownership_joint
      10 count_ownership_self
      11 count_ownership_spouse
      12 total_transaction_value
      13 average_transaction_amount
      14 avg_perf_7d
      15 avg_perf_30d
      16 avg_perf_current
      17 accuracy_7d
      18 accuracy_30d
      19 accuracy_current
      20 total_net_profit
      21 total_value
    Returns a list of 4 Embeds for pagination.
    """

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
        title=f"{name} Analytics (Page 1/4)",
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
        title=f"{name} Analytics (Page 2/4)",
        description="**Performance & Accuracy**",
        color=discord.Color.blue()
    )
    embed2.add_field(name="Avg Perf (7d)", value=f"{avg_perf_7d:.2f}%", inline=False)
    embed2.add_field(name="Avg Perf (30d)", value=f"{avg_perf_30d:.2f}%", inline=False)
    embed2.add_field(name="Avg Perf (Current)", value=f"{avg_perf_current:.2f}%", inline=False)
    embed2.add_field(name="Accuracy (7d)", value=f"{accuracy_7d:.2f}%", inline=False)
    embed2.add_field(name="Accuracy (30d)", value=f"{accuracy_30d:.2f}%", inline=False)
    embed2.add_field(name="Accuracy (Current)", value=f"{accuracy_current:.2f}%", inline=False)

    # ---------- PAGE 3 ----------
    embed3 = discord.Embed(
        title=f"{name} Analytics (Page 3/4)",
        description="**Transaction Counts**",
        color=discord.Color.blue()
    )
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
        title=f"{name} Analytics (Page 4/4)",
        description="**Ownership**",
        color=discord.Color.blue()
    )
    embed4.add_field(name="Self", value=f"{count_ownership_self:,}", inline=False)
    embed4.add_field(name="Spouse", value=f"{count_ownership_spouse:,}", inline=False)
    embed4.add_field(name="Joint", value=f"{count_ownership_joint:,}", inline=False)
    embed4.add_field(name="Child", value=f"{count_ownership_child:,}", inline=False)
    embed4.add_field(name="Dep. Child", value=f"{count_ownership_dependent_child:,}", inline=False)

    return [embed1, embed2, embed3, embed4]