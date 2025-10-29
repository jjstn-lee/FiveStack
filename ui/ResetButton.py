

import discord

from models import FiveManView


class ResetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Reset Group",
            style=discord.ButtonStyle.secondary,
            emoji="🔄",
            custom_id="reset_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view
        # print(f"=== RESET BUTTON CALLBACK DEBUG ===")
        # print(f"User: {interaction.user.id}")
        # print(f"Guild: {interaction.guild_id}")
        # print(f"Custom ID: {self.custom_id}")
        # print(f"View creator: {view.creator_id}")
        # print(f"View guild: {view.guild_id}")
        # print(f"View closed: {view.is_closed}")
        
        try:
            if view.is_closed:
                await interaction.response.send_message("❌ This group has been closed.", ephemeral=True)
                return
            
            # reset slots
            view.slots = [None] * 5
    
            embed = view.update_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            await interaction.followup.send("🔄 All slots have been reset!", ephemeral=True)           
        except Exception as e:
            print(f"Error in ResetButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)