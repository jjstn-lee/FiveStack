import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = False
intents.guilds = True
intents.members = True

# handle .env file
load_dotenv()
app_id = os.getenv("APP_ID")
discord_token = os.getenv("DISCORD_TOKEN")
public_key = os.getenv("PUBLIC_KEY")

bot = commands.Bot(command_prefix="!", intents=intents)

# Global variable to track active group
active_group = None

class FiveManView(discord.ui.View):
    def __init__(self, creator_id: int):
        super().__init__(timeout=3600)  # auto-timeout after 1 hour
        self.slots = [None] * 5  # 5 slots, initially empty
        self.creator_id = creator_id
        self.original_message = None
        self.is_closed = False

        # Add only ONE generic "Join Slot" button
        self.add_item(SlotButton()) # No slot_index needed for this single button
        
        # Add control buttons in second row
        self.add_item(ResetButton())
        self.add_item(LeaveButton())
        self.add_item(CloseGroupButton())

    def close_group(self):
        """Mark this group as closed and clear global reference"""
        global active_group
        self.is_closed = True
        if active_group == self:
            active_group = None

    def is_user_already_joined(self, user: discord.User):
        return user.id in [s["user"].id for s in self.slots if s]

    def get_user_slot(self, user: discord.User):
        for i, slot in enumerate(self.slots):
            if slot and slot["user"].id == user.id:
                return i
        return None

    def get_first_available_slot(self):
        """Returns the index of the first empty slot, or None if full."""
        for i, slot in enumerate(self.slots):
            if slot is None:
                return i
        return None

    def is_full(self):
        return all(slot is not None for slot in self.slots)

    def update_embed(self):
        filled_count = sum(1 for slot in self.slots if slot)
        remaining_count = 5 - filled_count
        
        # Create progress bar with emojis
        progress_bar = ""
        for i in range(5):
            if i < filled_count:
                progress_bar += "✅"
            else:
                progress_bar += "⬜"
        
        # Change color and title based on status
        if self.is_full():
            color = discord.Color.green()
            title = f"🎉 5 MAN GROUP - FULL! {progress_bar} {filled_count}/5"
        else:
            color = discord.Color.blurple()
            title = f"🧩 5 MAN PROGRESS: {progress_bar} {filled_count}/5"

        embed = discord.Embed(title=title, color=color)
        
        # Create a cleaner display - only show filled slots and remaining count
        description = ""
        
        # List filled slots
        filled_slots = [slot for slot in self.slots if slot]
        if filled_slots:
            description += "**Joined Players:**\n"
            for slot in filled_slots:
                time_text = f" - *{slot['time']}*" if slot['time'] else ""
                description += f"• {slot['user'].mention}{time_text}\n"
            description += "\n"
        
        # Show remaining slots count
        if remaining_count > 0:
            description += f"**Remaining Slots:** {remaining_count} (Open)\n"
        
        embed.description = description.strip()
        
        if self.is_full():
            embed.add_field(
                name="🎮 GROUP FULL!", 
                value="All 5 slots filled!.", 
                inline=False
            )
        else:
            embed.set_footer(text="Click 'Join Group' button below to join!") # Updated footer text
        
        return embed

    # async def on_timeout(self):
    #     global active_group
    #     try:
    #         # Disable all buttons when timeout occurs
    #         for item in self.children:
    #             item.disabled = True
            
    #         embed = discord.Embed(
    #             title="⏰ 5man Group - Expired", 
    #             description="This group finder has expired after 1 hour of inactivity.",
    #             color=discord.Color.red()
    #         )
            
    #         if self.original_message:
    #             await self.original_message.edit(embed=embed, view=self)
            
    #         # Clear global reference
    #         self.close_group()
            
    #     except Exception as e:
    #         print(f"Error in timeout handler: {e}")


class SlotButton(discord.ui.Button):
    def __init__(self): # Removed slot_index from __init__
        super().__init__(
            label="Join", # Changed label from "Join Slot" to "Join Group"
            style=discord.ButtonStyle.primary,
            emoji="🎮"
        )

    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view

        try:
            # Check if group is closed
            if view.is_closed:
                await interaction.response.send_message("❌ This group has been closed.", ephemeral=True)
                return
            
            # Check if user already joined another slot
            if view.is_user_already_joined(interaction.user):
                await interaction.response.send_message(
                    f"❗ You're already in the group. Use 'Leave' button first to update your availability.", 
                    ephemeral=True
                )
                return

            # Check if group is full before attempting to join
            if view.is_full():
                await interaction.response.send_message("❌ The group is currently full.", ephemeral=True)
                return
            
            # Ask user for optional time input
            await interaction.response.send_modal(
                TimeModal(
                    user=interaction.user,
                    view=view
                )
            )
        except Exception as e:
            print(f"Error in SlotButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)


class LeaveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Leave",
            style=discord.ButtonStyle.danger,
            emoji="🚪"
        )

    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view

        try:
            # Check if group is closed
            if view.is_closed:
                await interaction.response.send_message("❌ This group has been closed.", ephemeral=True)
                return
            
            user_slot = view.get_user_slot(interaction.user)
            
            if user_slot is None:
                await interaction.response.send_message("❗ You're not in any slot.", ephemeral=True)
                return

            # Remove user from their slot
            view.slots[user_slot] = None
            
            # Update the embed and view
            embed = view.update_embed()
            await view.original_message.edit(embed=embed, view=view)
            
            await interaction.response.send_message(f"✅ You left the group.", ephemeral=True)
            
        except Exception as e:
            print(f"Error in LeaveButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)


class ResetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Reset Group",
            style=discord.ButtonStyle.secondary,
            emoji="🔄"
        )

    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view

        try:
            # Check if group is closed
            if view.is_closed:
                await interaction.response.send_message("❌ This group has been closed.", ephemeral=True)
                return
            
            # Only creator can reset
            if interaction.user.id != view.creator_id:
                await interaction.response.send_message("❌ Only the person who started this group can reset it.", ephemeral=True)
                return

            # Reset all slots
            view.slots = [None] * 5
            
            # Update the embed and view
            embed = view.update_embed()
            await view.original_message.edit(embed=embed, view=view)
            
            await interaction.response.send_message("🔄 All slots have been reset!", ephemeral=True)
            
        except Exception as e:
            print(f"Error in ResetButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)


class CloseGroupButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Close Group",
            style=discord.ButtonStyle.danger,
            emoji="🔒"
        )

    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view
        global active_group

        try:
            # Check if group is already closed
            if view.is_closed:
                await interaction.response.send_message("❌ This group is already closed.", ephemeral=True)
                return
            
            # Only creator can close
            if interaction.user.id != view.creator_id:
                await interaction.response.send_message("❌ Only the person who started this group can close it.", ephemeral=True)
                return

            # Close the group
            view.close_group()
            
            # Disable all buttons
            for item in view.children:
                item.disabled = True
            
            # Update embed to show closed status
            embed = discord.Embed(
                title="🔒 5man Group - Closed",
                description="This group has been closed by the organizer.",
                color=discord.Color.red()
            )
            
            await view.original_message.edit(embed=embed, view=view)
            await interaction.response.send_message("🔒 Group has been closed. A new group can now be created.", ephemeral=True)
            
        except Exception as e:
            print(f"Error in CloseGroupButton callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)


class TimeModal(discord.ui.Modal, title="Join Slot"):
    time_input = discord.ui.TextInput(
        label="When are you available? (Optional)",
        required=False,
        placeholder="e.g. 7PM to 9PM EST, Now, etc.",
        max_length=100
    )

    def __init__(self, user, view):
        super().__init__()
        self.user = user
        self.view_ref = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Find the first available slot
            available_slot_index = self.view_ref.get_first_available_slot()

            if available_slot_index is None:
                await interaction.response.send_message("❌ No available slots found. The group might have just filled.", ephemeral=True)
                return

            # Fill the slot
            self.view_ref.slots[available_slot_index] = {
                "user": self.user,
                "time": self.time_input.value.strip() if self.time_input.value else None
            }

            # Update the embed
            embed = self.view_ref.update_embed()
            await self.view_ref.original_message.edit(embed=embed, view=self.view_ref)
            
            # Send confirmation
            time_msg = f" with availability: {self.time_input.value}" if self.time_input.value else ""
            await interaction.response.send_message(f"✅ Joined the group{time_msg}!", ephemeral=True)
            
            # If group is now full, notify everyone
            if self.view_ref.is_full():
                all_users = [slot["user"] for slot in self.view_ref.slots if slot]
                mentions = " ".join([user.mention for user in all_users])
                
                # Send a follow-up message to ping everyone
                try:
                    await interaction.followup.send(
                        f"🎉 **GROUP IS FULL!** {mentions}\nYour 5man is ready to go! Coordinate and have fun! 🎮",
                        ephemeral=False
                    )
                except:
                    # If followup fails, try to send in the channel
                    pass
            
        except Exception as e:
            print(f"Error in TimeModal on_submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)


@bot.tree.command(name="5man", description="Start a 5-man party finder")
async def five_man_command(interaction: discord.Interaction):
    global active_group
    
    try:
        # Check if there's already an active group
        if active_group and not active_group.is_closed:
            await interaction.response.send_message(
                "❌ There's already an active 5man group! Only one group can be active at a time.\n"
                "Ask the current organizer to close it first.",
                ephemeral=True
            )
            return
        
        # Create new group
        view = FiveManView(creator_id=interaction.user.id)
        active_group = view  # Set as the active group
        embed = view.update_embed()

        # Try to find the role
        role = discord.utils.get(interaction.guild.roles, name="league-of-legends")
        if role:
            ping=role.mention

        # Send the initial message
        await interaction.response.send_message(
            content=f"{ping} – New 5 man forming! 🎮",
            embed=embed,
            view=view
        )

        # Store the message reference for later editing
        view.original_message = await interaction.original_response()
        
    except Exception as e:
        print(f"Error in 5man command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Failed to create 5 man. Please try again.", ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔃 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

bot.run(discord_token)