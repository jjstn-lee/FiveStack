

import discord

from models import FiveManView


class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Close Group",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="close_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view
        # print(f"=== CLOSE GROUP BUTTON CALLBACK DEBUG ===")
        # print(f"User: {interaction.user.id}")
        # print(f"Guild: {interaction.guild_id}")
        # print(f"Custom ID: {self.custom_id}")
        # print(f"View creator: {view.creator_id}")
        # print(f"View guild: {view.guild_id}")
        # print(f"View closed: {view.is_closed}")
        
        try:
            if view.is_closed:
                await interaction.response.send_message("❌ This group is already closed.", ephemeral=True)
                return
            
            view.close_group()
            
            # disable all buttons
            for item in view.children:
                item.disabled = True
            
            embed = discord.Embed(
                title="🔒 FiveStack Group - Closed",
                description="This group has been closed by the organizer.",
                color=discord.Color.red()
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
            await interaction.followup.send("🔒 Group has been closed. A new group can now be created.", ephemeral=True)
            
        except Exception as e:
            print(f"Error in CloseGroupButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)