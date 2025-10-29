import discord

from models import FiveManView


class LeaveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Leave",
            style=discord.ButtonStyle.danger,
            emoji="🚪",
            custom_id="leave_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view
        # print(f"=== LEAVE BUTTON CALLBACK DEBUG ===")
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
            
            user_slot_index = None
            for i, slot in enumerate(view.slots):
                if slot and slot["user_id"] == interaction.user.id:
                    user_slot_index = i
                    break
            
            if user_slot_index is None:
                await interaction.response.send_message("❌ You're not in this group.", ephemeral=True)
                return
            
            view.slots[user_slot_index] = None
            
            embed = view.update_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            
            await interaction.followup.send("👋 You've left the group!", ephemeral=True)
            
        except Exception as e:
            print(f"❌ Exception in LeaveButton callback: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)
                except Exception as e2:
                    print(f"❌ Failed to send error response: {e2}")