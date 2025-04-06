import discord
from discord.ext import commands
from discord import app_commands
from modules.config import (
    DISCORD_BOT_GUILD_ID,
    SUBSCRIBE_VIP_ROLE_ID,
    SUBSCRIBE_LIFETIME_ROLE_ID,
    SUBSCRIBE_INFO_CHANNEL_ID,
    KOFI_SHOP_STORE_LINK
)
from bot_modules.bot_utilis import in_bot_commands_channel

class SubscribeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @in_bot_commands_channel()
    @app_commands.guilds(discord.Object(id=DISCORD_BOT_GUILD_ID))
    @app_commands.command(name="subscribe", description="Learn how to subscribe for detailed analytics.")
    async def subscribe(self, interaction: discord.Interaction):
        # Create role and channel mentions using their IDs
        vip_role_mention = f"<@&{SUBSCRIBE_VIP_ROLE_ID}>"
        lifetime_role_mention = f"<@&{SUBSCRIBE_LIFETIME_ROLE_ID}>"
        subscribe_channel_mention = f"<#{SUBSCRIBE_INFO_CHANNEL_ID}>"

        embed = discord.Embed(
            title="Subscribe for Detailed Analytics",
            description=(
                "Subscribe in order to gain access to our detailed analytics.\n\n"
                f"{vip_role_mention} - $10/month\n"
                f"{lifetime_role_mention} - $100\n\n"
                "While both roles offer the same benefits, the Lifetime option guarantees you "
                "permanent access to all of our services, including our analytics website *(in development)* "
                "and any future datasets and analytics.\n\n"
                "As our service grows, the monthly subscription costs may change.\n"
                f"Read more about the benefits in {subscribe_channel_mention} channel or [here]({KOFI_SHOP_STORE_LINK})!"
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SubscribeCog(bot))
