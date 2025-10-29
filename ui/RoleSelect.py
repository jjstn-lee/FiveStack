

import discord

from ui.TimeModal import TimeModal


class RoleSelect(discord.ui.View):
    def __init__(self, user, parent_view):
        super().__init__(timeout=60)
        self.user = user
        self.parent_view = parent_view
        self.selected_role = None
    
    @discord.ui.select(
        placeholder="Select your preferred role",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Top", emoji="<:top_lane:1403834039735025674>"),
            discord.SelectOption(label="Jungle", emoji="<:jungle:1403834034957713691>"),
            discord.SelectOption(label="Mid", emoji="<:mid_lane:1403834037776154785>"),
            discord.SelectOption(label="ADC", emoji="<:bot_lane:1403834041010098246>"),
            discord.SelectOption(label="Support", emoji="<:support:1403834038694973521>"),
            discord.SelectOption(label="Fill", emoji="<:fill:1403834036866125884>"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_role = select.values[0]
        await interaction.response.send_modal(TimeModal(self.user, self.parent_view, self.selected_role))
        self.stop()