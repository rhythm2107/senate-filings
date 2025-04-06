# bot_modules/custom_exceptions.py
from discord.app_commands import AppCommandError

class WrongChannelError(AppCommandError):
    """Raised when a user is in the wrong channel for a command."""

class MissingVIPRoleError(AppCommandError):
    """Raised when a user doesn't have the VIP role."""