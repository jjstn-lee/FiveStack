import discord

class TimeModal(discord.ui.Modal, title="Join Slot"):
    time_input = discord.ui.TextInput(
        label="When are you available? (Optional)",
        required=False,
        placeholder="e.g. 7PM to 9PM EST, now, etc.",
        max_length=100
    )
    
    def __init__(self, user, view, role):
        super().__init__()
        self.user = user
        self.view_ref = view
        self.selected_role = role
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            available_slot_index = self.view_ref.get_first_available_slot()
            if available_slot_index is None:
                await interaction.response.send_message(
                    "❌ No available slots found. The group might have just filled.",
                    ephemeral=True
                )
                return
            
            self.view_ref.slots[available_slot_index] = {
                "user_id": self.user.id,
                "username": self.user.display_name,
                "time": self.time_input.value.strip() if self.time_input.value else None,
                "role": self.selected_role
            }
            
            embed = self.view_ref.update_embed()
            
            details = []
            if self.time_input.value:
                details.append(f"availability: {self.time_input.value}")
            if self.selected_role:
                details.append(f"role: {self.selected_role}")
            detail_msg = " with " + ", ".join(details) if details else ""
            
            await interaction.response.send_message(f"✅ Joined the group{detail_msg}!", ephemeral=True)
            
            # edit ORIGINAL message, NOT the interaction; that will cause the ephemeral to have the updated view
            if hasattr(self.view_ref, 'original_message') and self.view_ref.original_message:
                await self.view_ref.original_message.edit(embed=embed, view=self.view_ref)
            
            if self.view_ref.is_full():
                user_ids = [slot["user_id"] for slot in self.view_ref.slots if slot]
                mentions = " ".join([f"<@{user_id}>" for user_id in user_ids])
                # send the "group full" message to the channel (not ephemeral)
                await self.view_ref.original_message.channel.send(
                    f"🎉 **GROUP IS FULL!** {mentions}\nYour 5-man is ready to go! Coordinate and have fun! 🎮"
                )
                
        except Exception as e:
            print(f"Error in TimeModal on_submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)