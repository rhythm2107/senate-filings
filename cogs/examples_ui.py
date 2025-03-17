import discord
from discord.ext import commands
from discord import app_commands
from modules.config import DISCORD_BOT_GUILD_ID

# Replace with the actual guild ID for testing
GUILD_ID = DISCORD_BOT_GUILD_ID

class UIExamples(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 1) Simple ephemeral message
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="demo_ephemeral", description="Send an ephemeral message.")
    async def demo_ephemeral(self, interaction: discord.Interaction):
        """Sends an ephemeral message only visible to you."""
        await interaction.response.send_message(
            "This message is ephemeral. Only you can see it!",
            ephemeral=True
        )

    # 2) Buttons example
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="demo_buttons", description="Show a message with interactive buttons.")
    async def demo_buttons(self, interaction: discord.Interaction):
        """Sends a message with two buttons."""
        view = ButtonDemoView()
        await interaction.response.send_message(
            "Here are two buttons!",
            view=view
        )

    # 3) Select menu example
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="demo_select", description="Show a dropdown select menu.")
    async def demo_select(self, interaction: discord.Interaction):
        """Sends a message with a select menu (dropdown)."""
        view = SelectDemoView()
        await interaction.response.send_message(
            "Pick an option from the dropdown!",
            view=view
        )

    # 4) Modal (pop-up form) example
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="demo_modal", description="Show a modal pop-up for user input.")
    async def demo_modal(self, interaction: discord.Interaction):
        """Displays a modal for the user to fill out."""
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)

# -------------------------------------------------------------------
# Below are the UI classes: a button view, a select menu view, and a modal
# -------------------------------------------------------------------

class ButtonDemoView(discord.ui.View):
    """A view containing two buttons."""

    @discord.ui.button(label="Hello", style=discord.ButtonStyle.primary)
    async def hello_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You clicked the 'Hello' button!", ephemeral=True)

    @discord.ui.button(label="Goodbye", style=discord.ButtonStyle.danger)
    async def goodbye_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You clicked the 'Goodbye' button!", ephemeral=True)

class SelectDemoView(discord.ui.View):
    """A view containing a single select (dropdown) menu."""
    def __init__(self):
        super().__init__()
        # Add the select menu to the view
        self.add_item(MySelect())

class MySelect(discord.ui.Select):
    """A custom select menu for demonstration."""

    def __init__(self):
        options = [
            discord.SelectOption(label="Option A", description="First option"),
            discord.SelectOption(label="Option B", description="Second option"),
            discord.SelectOption(label="Option C", description="Third option"),
            discord.SelectOption(label="Option D", description="Third option"),
            discord.SelectOption(label="Option E", description="Third option"),
            discord.SelectOption(label="Option F", description="Third option"),
            discord.SelectOption(label="Option G", description="Third option"),
            discord.SelectOption(label="Option H", description="Third option"),
            discord.SelectOption(label="Option J", description="Third option"),
            discord.SelectOption(label="Option K", description="Third option"),
            discord.SelectOption(label="Option L", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
            # discord.SelectOption(label="Option C", description="Third option"),
        ]
        super().__init__(
            placeholder="Choose an option...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback when user picks an option from the dropdown."""
        chosen = self.values[0]
        await interaction.response.send_message(f"You picked: {chosen}", ephemeral=True)

class FeedbackModal(discord.ui.Modal, title="User Feedback"):
    """A modal with a single text input."""

    # Define a text input field
    feedback = discord.ui.TextInput(
        label="Your Feedback",
        style=discord.TextStyle.long,
        placeholder="Enter your feedback here...",
        required=True,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Called when the user submits the modal."""
        # 'self.feedback.value' contains whatever the user typed
        await interaction.response.send_message(
            f"Thank you for your feedback!\nYou said: {self.feedback.value}",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    """Standard setup function to add this cog to the bot."""
    await bot.add_cog(UIExamples(bot))
