import discord

def create_embed_senator_list(page: int, pages: int, senators: list):
    embed = discord.Embed(
        title=f"Senators List (Page {page + 1}/{pages})",
        color=discord.Color.blue()
    )
    for senator_id, name in senators:
        embed.add_field(name=f"ID: {senator_id}", value=name, inline=False)
    return embed