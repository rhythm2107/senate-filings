from discord import app_commands
import discord
from discord.ext import commands
from modules.config import DISCORD_BOT_CMD_CHANNEL_ID


# Functions returning mappings
def get_leaderboard_column_map() -> dict[str, str]:
    """
    Return a dict mapping user-friendly labels (e.g. 'Total Volume')
    to actual analytics column names (e.g. 'total_transaction_value').
    """
    return {
        "Total Volume": "total_transaction_value",
        "Total Transactions": "total_transaction_count",
        "Average Transaction": "average_transaction_amount",
        "Average Gain (7 Days)": "avg_perf_7d",
        "Average Gain (30 Days)": "avg_perf_30d",
        "Average Gain (All Time)": "avg_perf_current",
        "Accuracy (7 Days)": "accuracy_7d",
        "Accuracy (30 Days)": "accuracy_30d",
        "Accuracy (All Time)": "accuracy_current",
        "Net Worth": "total_value",
    }

def get_stock_requirement_columns() -> set[str]:
    """
    Return the set of columns that require total_stock_transactions >= 30.
    """
    return {
        "avg_perf_7d", "avg_perf_30d", "avg_perf_current",
        "accuracy_7d", "accuracy_30d", "accuracy_current"
    }

def get_leaderboard_choices() -> list[app_commands.Choice]:
    """
    Return the list of app_commands.Choice used in the slash command.
    """
    # We'll build it from our column map keys, so everything stays in sync.
    # If you want them in a specific order, define them manually or sort them.
    column_map = get_leaderboard_column_map()
    friendly_labels = list(column_map.keys())
    # You can manually reorder or just keep them in the dict's iteration order.

    # Convert each label to a Choice
    choices = [app_commands.Choice(name=label, value=label) for label in friendly_labels]
    return choices

def format_leaderboard_value(value: float, db_column: str) -> str:
    """
    Format numeric value for displaying in the leaderboard.
      - Perf/Accuracy => 'xx.xx%'
      - total_transaction_count => int with commas
      - total_value / total_transaction_value / average_transaction_amount => integer + commas + '$'
      - else => .2f with commas
    """
    stock_req = get_stock_requirement_columns()

    if db_column in stock_req:
        # perf/accuracy
        return f"{value:.2f}%"

    if db_column == "total_transaction_count":
        return f"{int(value):,}"

    if db_column in {"total_value", "total_transaction_value", "average_transaction_amount"}:
        return f"${int(value):,}"

    # fallback => .2f with commas
    return f"{value:,.2f}"


# Decorator for checking if the command is used in a designated channel
def in_designated_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel and interaction.channel.id == DISCORD_BOT_CMD_CHANNEL_ID:
            return True
        # If not, send an ephemeral message and prevent command execution.
        await interaction.response.send_message(
            "This command can only be used in the designated bot-command channel.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

# Define a custom check function for required roles
def has_required_role(interaction: discord.Interaction) -> bool:
    # List of allowed role names
    allowed_roles = {"Admin", "Moderator"}
    # Ensure the interaction's user has at least one of the allowed roles
    return any(role.name in allowed_roles for role in interaction.user.roles)