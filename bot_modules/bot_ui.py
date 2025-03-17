import discord

class PaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author_id: int):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0
        self.message = None
        self.author_id = author_id

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

class AnalyticsPaginatorView(discord.ui.View):
    """
    A generic 4-page paginator for the embed list created by build_analytics_embeds.
    """
    def __init__(self, embeds: list[discord.Embed], author_id: int):
        super().__init__(timeout=180)
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