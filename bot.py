import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
import time
from datetime import datetime, timedelta
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

group = discord.app_commands.Group(name="5man", description="Commands for 5man")

# Session persistence file
SESSION_FILE = "session_data.json"

class SessionManager:
    """Handles saving and loading session data"""
    
    @staticmethod
    def save_session(view_data):
        """Save session data to file"""
        try:
            data = {
                "timestamp": time.time(),
                "guild_id": view_data["guild_id"],
                "channel_id": view_data["channel_id"],
                "message_id": view_data["message_id"],
                "creator_id": view_data["creator_id"],
                "slots": view_data["slots"],
                "is_closed": view_data["is_closed"],
                "created_at": view_data["created_at"]
            }
            
            with open(SESSION_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Session saved at {datetime.now()}")
            
        except Exception as e:
            print(f"❌ Error saving session: {e}")
    
    @staticmethod
    def load_session():
        """Load session data from file"""
        try:
            if not os.path.exists(SESSION_FILE):
                return None
                
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
            
            # Check if session is too old (older than 1 hour)
            session_age = time.time() - data["timestamp"]
            if session_age > 3600:  # 1 hour
                print("⏰ Session too old, ignoring")
                SessionManager.clear_session()
                return None
            
            print(f"✅ Session loaded from {datetime.fromtimestamp(data['timestamp'])}")
            return data
            
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return None
    
    @staticmethod
    def clear_session():
        """Clear session file"""
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
                print("🗑️ Session file cleared")
        except Exception as e:
            print(f"❌ Error clearing session: {e}")

class FiveManView(discord.ui.View):
    def __init__(self, creator_id: int, restore_data=None):
        super().__init__(timeout=None)  # No timeout - we'll handle refreshing manually
        self.creator_id = creator_id
        self.original_message = None
        self.is_closed = False
        self.created_at = restore_data.get("created_at", time.time()) if restore_data else time.time()
        self.last_refresh = time.time()
        
        # Restore slots if provided, otherwise initialize empty
        if restore_data and restore_data.get("slots"):
            self.slots = restore_data["slots"]
            self.is_closed = restore_data.get("is_closed", False)
        else:
            self.slots = [None] * 5  # 5 slots, initially empty

        # Add buttons with custom_id for persistence
        self.add_item(SlotButton())
        self.add_item(ResetButton())
        self.add_item(LeaveButton())
        self.add_item(CloseGroupButton())

    def save_state(self):
        """Save current state to file"""
        if self.original_message:
            view_data = {
                "guild_id": self.original_message.guild.id,
                "channel_id": self.original_message.channel.id,
                "message_id": self.original_message.id,
                "creator_id": self.creator_id,
                "slots": self.slots,
                "is_closed": self.is_closed,
                "created_at": self.created_at
            }
            SessionManager.save_session(view_data)

    async def refresh_view(self):
        """Refresh the view to prevent 15-minute timeout"""
        try:
            if self.is_closed or not self.original_message:
                return
            
            # Check if it's been more than 14 minutes since last refresh
            if time.time() - self.last_refresh > 840:  # 14 minutes
                print("🔄 Refreshing view to prevent timeout...")
                
                # Create a new view with the same data
                new_view = FiveManView(self.creator_id, {
                    "slots": self.slots,
                    "is_closed": self.is_closed,
                    "created_at": self.created_at
                })
                new_view.original_message = self.original_message
                new_view.last_refresh = time.time()
                
                # Update global reference
                global active_group
                active_group = new_view
                
                # Update the message with the new view
                embed = new_view.update_embed()
                await self.original_message.edit(embed=embed, view=new_view)
                
                print("✅ View refreshed successfully")
                
        except Exception as e:
            print(f"❌ Error refreshing view: {e}")

    def close_group(self):
        """Mark this group as closed and clear global reference"""
        global active_group
        self.is_closed = True
        if active_group == self:
            active_group = None
        # Clear session when group is closed
        SessionManager.clear_session()

    def is_user_already_joined(self, user: discord.User):
        return any(slot and slot["user_id"] == user.id for slot in self.slots if slot)

    def get_user_slot(self, user: discord.User):
        for i, slot in enumerate(self.slots):
            if slot and slot["user_id"] == user.id:
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
                # Try to get user mention, fallback to username if user not found
                try:
                    user = bot.get_user(slot["user_id"])
                    user_mention = user.mention if user else f"<@{slot['user_id']}>"
                except:
                    user_mention = slot.get("username", f"<@{slot['user_id']}>")
                
                time_text = f" - *{slot['time']}*" if slot['time'] else ""
                description += f"• {user_mention}{time_text}\n"
            description += "\n"
        
        # Show remaining slots count
        if remaining_count > 0:
            description += f"**Remaining Slots:** {remaining_count} (Open)\n"
        
        embed.description = description.strip()
        
        if self.is_full():
            embed.add_field(
                name="🎮 GROUP FULL!", 
                value="All 5 slots filled!", 
                inline=False
            )
        else:
            embed.set_footer(text="Click 'Join' button below to join!")
        
        # Add session info
        session_age = time.time() - self.created_at
        session_minutes = int(session_age / 60)
        embed.set_footer(text=f"Group active for {session_minutes} minutes | Auto-refreshes to stay active")
        
        return embed


class SlotButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Join",
            style=discord.ButtonStyle.primary,
            emoji="🎮",
            custom_id="join_slot_button"  # Persistent custom_id
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
            emoji="🚪",
            custom_id="leave_button"
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
            
            # Save state after change
            view.save_state()
            
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
            emoji="🔄",
            custom_id="reset_button"
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
            
            # Save state after change
            view.save_state()
            
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
            emoji="🔒",
            custom_id="close_button"
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

            # Fill the slot with serializable data
            self.view_ref.slots[available_slot_index] = {
                "user_id": self.user.id,
                "username": self.user.display_name,
                "time": self.time_input.value.strip() if self.time_input.value else None
            }

            # Update the embed
            embed = self.view_ref.update_embed()
            await self.view_ref.original_message.edit(embed=embed, view=self.view_ref)
            
            # Save state after change
            self.view_ref.save_state()
            
            # Send confirmation
            time_msg = f" with availability: {self.time_input.value}" if self.time_input.value else ""
            await interaction.response.send_message(f"✅ Joined the group{time_msg}!", ephemeral=True)
            
            # If group is now full, notify everyone
            if self.view_ref.is_full():
                user_ids = [slot["user_id"] for slot in self.view_ref.slots if slot]
                mentions = " ".join([f"<@{user_id}>" for user_id in user_ids])
                
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


# Background task to refresh views and prevent 15-minute timeout
@tasks.loop(minutes=10)  # Check every 10 minutes
async def refresh_active_views():
    """Background task to refresh views before they timeout"""
    global active_group
    
    if active_group and not active_group.is_closed:
        await active_group.refresh_view()


@group.command(name="start", description="Start a 5-man party finder")
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
        ping = role.mention if role else ""

        # Send the initial message
        await interaction.response.send_message(
            content=f"{ping} – New 5 man forming! 🎮",
            embed=embed,
            view=view
        )

        # Store the message reference for later editing
        view.original_message = await interaction.original_response()
        
        # Save initial state
        view.save_state()
        
        # Start the refresh task if it's not already running
        if not refresh_active_views.is_running():
            refresh_active_views.start()
        
    except Exception as e:
        print(f"Error in 5man command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Failed to create 5 man. Please try again.", ephemeral=True)
            
async def restore_session():
    """Restore session from saved data on bot startup"""
    global active_group
    
    session_data = SessionManager.load_session()
    if not session_data:
        return
    
    try:
        # Get the guild and channel
        guild = bot.get_guild(session_data["guild_id"])
        if not guild:
            print("❌ Guild not found, cannot restore session")
            SessionManager.clear_session()
            return
        
        channel = guild.get_channel(session_data["channel_id"])
        if not channel:
            print("❌ Channel not found, cannot restore session")
            SessionManager.clear_session()
            return
        
        # Try to get the original message
        try:
            message = await channel.fetch_message(session_data["message_id"])
        except discord.NotFound:
            print("❌ Original message not found, cannot restore session")
            SessionManager.clear_session()
            return
        
        # Create a new view with restored data
        view = FiveManView(session_data["creator_id"], restore_data=session_data)
        view.original_message = message
        active_group = view
        
        # Update the message with the restored view
        embed = view.update_embed()
        await message.edit(embed=embed, view=view)
        
        # Start the refresh task
        if not refresh_active_views.is_running():
            refresh_active_views.start()
        
        print(f"✅ Session restored! Group has {sum(1 for slot in view.slots if slot)}/5 members")
        
    except Exception as e:
        print(f"❌ Error restoring session: {e}")
        SessionManager.clear_session()


@group.command(name="session", description="Check current session status")
async def session_status(interaction: discord.Interaction):
    """Debug command to check session status"""
    global active_group
    
    if active_group:
        filled_count = sum(1 for slot in active_group.slots if slot)
        session_age = time.time() - active_group.created_at
        session_minutes = int(session_age / 60)
        last_refresh_age = int((time.time() - active_group.last_refresh) / 60)
        
        await interaction.response.send_message(
            f"📊 **Session Status:**\n"
            f"• Active group: Yes\n"
            f"• Members: {filled_count}/5\n"
            f"• Age: {session_minutes} minutes\n"
            f"• Last refresh: {last_refresh_age} minutes ago\n"
            f"• Creator: <@{active_group.creator_id}>\n"
            f"• Closed: {'Yes' if active_group.is_closed else 'No'}\n"
            f"• Refresh task running: {'Yes' if refresh_active_views.is_running() else 'No'}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("📊 No active session found.", ephemeral=True)


@group.command(name="force_refresh", description="Manually refresh the current group (debug)")
async def force_refresh(interaction: discord.Interaction):
    """Manual refresh command for debugging"""
    global active_group
    
    if not active_group or active_group.is_closed:
        await interaction.response.send_message("❌ No active group to refresh.", ephemeral=True)
        return
    
    try:
        await active_group.refresh_view()
        await interaction.response.send_message("✅ Group view refreshed manually!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error refreshing: {e}", ephemeral=True)

bot.tree.add_command(group)

@bot.event
async def on_message(message):
    # Ignore bot and system messages
    if message.author.bot:
        return
    # If message starts with slash, it's likely not a valid user message anyway
    if not message.content.startswith("/"):
        await message.delete()
    else:
        print(f"message valid: {message}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔃 Synced {len(synced)} command(s)")
        
        # Restore session after bot is ready
        await restore_session()
        
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

bot.run(discord_token)