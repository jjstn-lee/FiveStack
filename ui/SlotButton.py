
import discord

from models import FiveManView
from ui.RoleSelect import RoleSelect


class SlotButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Join",
            style=discord.ButtonStyle.primary,
            emoji="🎮",
            custom_id="join_slot_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view
        # print(f"=== SLOT BUTTON CALLBACK DEBUG ===")
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
            
            if view.is_user_already_joined(interaction.user):
                await interaction.response.send_message(
                    f"❗ You're already in the group. Use 'Leave' button first to update your availability.",
                    ephemeral=True
                )
                return
            
            if view.is_full():
                await interaction.response.send_message("❌ The group is currently full.", ephemeral=True)
                return
            
            # RoleSelectView first, then open TimeModal to avoid answering same interaction twice
            role_select_view = RoleSelect(user=interaction.user, parent_view=view)
            await interaction.response.send_message(
                "Please select your League of Legends role first:",
                view=role_select_view,
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in SlotButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)