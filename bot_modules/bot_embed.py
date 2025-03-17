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


def safe_int(value):
    if value is None:
        return "N/A"
    return f"{int(value):,}"

def safe_float(value, suffix=""):
    if value is None:
        return "N/A"
    return f"{value:.2f}{suffix}"

def build_analytics_embeds(name: str, row: tuple) -> list[discord.Embed]:
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

    # Page 1
    embed1 = discord.Embed(
        title=f"{name} Analytics (Page 1/4)",
        description="Transaction Value & Net Profit",
        color=discord.Color.blue()
    )
    embed1.add_field(name="Total Transaction Value", value=f"${safe_int(total_transaction_value)}", inline=False)
    embed1.add_field(name="Average Transaction Amount", value=f"${safe_int(average_transaction_amount)}", inline=False)
    embed1.add_field(name="Total Net Profit", value=f"${safe_int(total_net_profit)}", inline=False)
    embed1.add_field(name="Total Value", value=f"${safe_int(total_value)}", inline=False)

    # Page 2
    embed2 = discord.Embed(
        title=f"{name} Analytics (Page 2/4)",
        description="Performance & Accuracy",
        color=discord.Color.blue()
    )
    embed2.add_field(name="Avg Perf (7d)", value=safe_float(avg_perf_7d, suffix="%"), inline=False)
    embed2.add_field(name="Avg Perf (30d)", value=safe_float(avg_perf_30d, suffix="%"), inline=False)
    embed2.add_field(name="Avg Perf (Current)", value=safe_float(avg_perf_current, suffix="%"), inline=False)
    embed2.add_field(name="Accuracy (7d)", value=safe_float(accuracy_7d, suffix="%"), inline=False)
    embed2.add_field(name="Accuracy (30d)", value=safe_float(accuracy_30d, suffix="%"), inline=False)
    embed2.add_field(name="Accuracy (Current)", value=safe_float(accuracy_current, suffix="%"), inline=False)

    # Page 3
    embed3 = discord.Embed(
        title=f"{name} Analytics (Page 3/4)",
        description="Transaction Counts",
        color=discord.Color.blue()
    )
    embed3.add_field(name="Total Transaction Count", value=safe_int(total_transaction_count), inline=False)
    embed3.add_field(name="Purchases", value=safe_int(total_purchase_count), inline=False)
    embed3.add_field(name="Sales", value=safe_int(total_sale_count), inline=False)
    embed3.add_field(name="Exchanges", value=safe_int(total_exchange_count), inline=False)
    embed3.add_field(name="Stock Transactions", value=safe_int(total_stock_transactions), inline=False)
    embed3.add_field(name="Other Transactions", value=safe_int(total_other_transactions), inline=False)

    # Page 4
    embed4 = discord.Embed(
        title=f"{name} Analytics (Page 4/4)",
        description="Ownership",
        color=discord.Color.blue()
    )
    embed4.add_field(name="Self", value=safe_int(count_ownership_self), inline=False)
    embed4.add_field(name="Spouse", value=safe_int(count_ownership_spouse), inline=False)
    embed4.add_field(name="Joint", value=safe_int(count_ownership_joint), inline=False)
    embed4.add_field(name="Child", value=safe_int(count_ownership_child), inline=False)
    embed4.add_field(name="Dep. Child", value=safe_int(count_ownership_dependent_child), inline=False)

    return [embed1, embed2, embed3, embed4]


