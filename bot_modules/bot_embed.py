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
