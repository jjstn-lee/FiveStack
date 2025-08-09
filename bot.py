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
# env = os.getenv("ENV")
# dev_guild_id = os.getenv("DEV_GUILD_ID")

bot = commands.Bot(command_prefix="!", intents=intents)

# Global variable to track active group
active_group = None

group = discord.app_commands.Group(name="5man", description="Commands for 5man")

class FiveManView(discord.ui.View):
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)  # No timeout - we'll handle refreshing manually
        self.creator_id = creator_id
        self.original_message = None
        self.is_closed = False
        self.created_at = time.time()
        self.last_refresh = time.time()
        
        self.slots = [None] * 5  # 5 slots, initially empty

        # Add buttons with custom_id for persistence
        self.add_item(SlotButton())
        self.add_item(ResetButton())
        self.add_item(LeaveButton())
        self.add_item(CloseGroupButton())
        
    def close_group(self):
        """Mark this group as closed and clear global reference"""
        global active_group
        self.is_closed = True
        if active_group == self:
            active_group = None
        # Clear session when group is closed

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
        
        # Add session info (mostly used for debugging)
        session_age = time.time() - self.created_at
        session_minutes = int(session_age / 60)
        
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

        print(f"=== SLOT BUTTON CALLBACK DEBUG ===")
        print(f"User: {interaction.user.id}")
        print(f"Custom ID: {self.custom_id}")
        print(f"View creator: {view.creator_id}")
        print(f"View closed: {view.is_closed}")
        print(f"Interaction token valid: {not interaction.is_expired()}")
        print(f"Bot user: {interaction.client.user.id}")
            
        
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
        print(f"=== LEAVE BUTTON CALLBACK DEBUG ===")
        print(f"User: {interaction.user.id}")
        print(f"Custom ID: {self.custom_id}")
        print(f"View creator: {view.creator_id}")
        print(f"View closed: {view.is_closed}")
        print(f"Interaction token valid: {not interaction.is_expired()}")
        print(f"Bot user: {interaction.client.user.id}")
            
        try:
            # Check if group is closed
            if view.is_closed:
                await interaction.response.send_message("❌ This group has been closed.", ephemeral=True)
                return
            
            # Find user's slot
            user_slot_index = None
            for i, slot in enumerate(view.slots):
                if slot and slot["user_id"] == interaction.user.id:
                    user_slot_index = i
                    break
            
            if user_slot_index is None:
                await interaction.response.send_message("❌ You're not in this group.", ephemeral=True)
                return
            
            # Remove user from slot
            view.slots[user_slot_index] = None
            
            # Update the embed and respond to the interaction (this is your one response)
            embed = view.update_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Send confirmation as a followup (not a response)
            await interaction.followup.send("👋 You've left the group!", ephemeral=True)
            
        except Exception as e:
            print(f"❌ Exception in LeaveButton callback: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)
                except Exception as e2:
                    print(f"❌ Failed to send error response: {e2}")

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

        print(f"=== RESET BUTTON CALLBACK DEBUG ===")
        print(f"User: {interaction.user.id}")
        print(f"Custom ID: {self.custom_id}")
        print(f"View creator: {view.creator_id}")
        print(f"View closed: {view.is_closed}")
        print(f"Interaction token valid: {not interaction.is_expired()}")
        print(f"Bot user: {interaction.client.user.id}")
        
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
            
            # Update the embed and respond to the interaction (this is your one response)
            embed = view.update_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Send confirmation as a followup (not a response)
            await interaction.followup.send("🔄 All slots have been reset!", ephemeral=True)
            
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
        
        print(f"=== CLOSE GROUP BUTTON CALLBACK DEBUG ===")
        print(f"User: {interaction.user.id}")
        print(f"Custom ID: {self.custom_id}")
        print(f"View creator: {view.creator_id}")
        print(f"View closed: {view.is_closed}")
        print(f"Interaction token valid: {not interaction.is_expired()}")
        print(f"Bot user: {interaction.client.user.id}")

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
            
            # Use interaction.response to edit the message (this is your one response)
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Send confirmation as a followup (not a response)
            await interaction.followup.send("🔒 Group has been closed. A new group can now be created.", ephemeral=True)
            
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

    role_select = discord.ui.Select(
        placeholder="Select your preferred role (Optional)",
        min_values=0,
        max_values=1,
        options=[
            discord.SelectOption(label="Top", emoji="🗻"),
            discord.SelectOption(label="Jungle", emoji="🌲"),
            discord.SelectOption(label="Mid", emoji="🛡️"),
            discord.SelectOption(label="ADC", emoji="🏹"),
            discord.SelectOption(label="Support", emoji="💖"),
        ]
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
                await interaction.response.send_message(
                    "❌ No available slots found. The group might have just filled.",
                    ephemeral=True
                )
                return

            # Fill the slot with serializable data
            self.view_ref.slots[available_slot_index] = {
                "user_id": self.user.id,
                "username": self.user.display_name,
                "time": self.time_input.value.strip() if self.time_input.value else None,
                "role": self.role_input.value.strip() if self.role_input.value else None
            }

            # Update the embed and respond
            embed = self.view_ref.update_embed()
            details = []
            if self.time_input.value:
                details.append(f"availability: {self.time_input.value}")
            if self.role_input.value:
                details.append(f"role: {self.role_input.value}")
            detail_msg = " with " + ", ".join(details) if details else ""

            await interaction.response.edit_message(embed=embed, view=self.view_ref)

            await interaction.followup.send(f"✅ Joined the group{detail_msg}!", ephemeral=True)

            # If group is now full, notify everyone
            if self.view_ref.is_full():
                user_ids = [slot["user_id"] for slot in self.view_ref.slots if slot]
                mentions = " ".join([f"<@{user_id}>" for user_id in user_ids])
                try:
                    await interaction.followup.send(
                        f"🎉 **GROUP IS FULL!** {mentions}\nYour 5-man is ready to go! Coordinate and have fun! 🎮",
                        ephemeral=False
                    )
                except Exception as e:
                    print(f"Failed to send full group notification: {e}")

        except Exception as e:
            print(f"Error in TimeModal on_submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)



# Background task to refresh views and prevent 15-minute timeout
# @tasks.loop(minutes=10)  # Check every 10 minutes
# async def refresh_active_views():
#     """Background task to refresh views before they timeout"""
#     global active_group
    
#     if active_group and not active_group.is_closed:
#         await active_group.refresh_view()



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
        
        # ⭐ CRITICAL: Register the view instance with the bot
        bot.add_view(view)
        
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
        
        # Save initial state (if you're keeping this for some reason)
        
        # Start the refresh task if it's not already running
        # if not refresh_active_views.is_running():
        #     refresh_active_views.start()
        
    except Exception as e:
        print(f"Error in 5man command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Failed to create 5 man. Please try again.", ephemeral=True)
            

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
            f"• Closed: {'Yes' if active_group.is_closed else 'No'}\n",
            # f"• Refresh task running: {'Yes' if refresh_active_views.is_running() else 'No'}",
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


async def cleanup_old_messages():
    """Delete any existing bot messages on startup"""
    try:
        import asyncio
        deleted_total = 0
        
        print("🧹 Starting message cleanup...")
        
        # Loop through all guilds the bot is in
        for guild in bot.guilds:
            # Loop through all channels the bot can see
            for channel in guild.text_channels:
                # Check if bot has permission to read message history and delete messages
                permissions = channel.permissions_for(guild.me)
                if not (permissions.read_message_history and permissions.manage_messages):
                    continue
                
                try:
                    deleted_count = 0
                    async for message in channel.history(limit=20):  # Reduced limit
                        if message.author == bot.user:
                            try:
                                await message.delete()
                                deleted_count += 1
                                # Add delay between deletions to avoid rate limiting
                                await asyncio.sleep(0.5)  # 500ms delay between deletions
                            except discord.NotFound:
                                # Message already deleted
                                pass
                            except discord.Forbidden:
                                # Lost permissions mid-cleanup
                                break
                            except discord.HTTPException as e:
                                if e.status == 429:  # Rate limited
                                    print(f"⏳ Rate limited, waiting...")
                                    await asyncio.sleep(2)  # Wait 2 seconds on rate limit
                                    continue
                                else:
                                    raise
                    
                    if deleted_count > 0:
                        print(f"🧹 Cleaned up {deleted_count} old bot message(s) from #{channel.name} in {guild.name}")
                        deleted_total += deleted_count
                    
                    # Add delay between channels
                    if deleted_count > 0:
                        await asyncio.sleep(1)  # 1 second delay between channels that had deletions
                        
                except discord.Forbidden:
                    # Don't have permission to read this channel
                    continue
                except Exception as e:
                    print(f"❌ Error cleaning up #{channel.name} in {guild.name}: {e}")
        
        if deleted_total > 0:
            print(f"🧹 Total cleanup: {deleted_total} message(s) deleted")
        else:
            print("✅ No old bot messages found to clean up")
        
    except Exception as e:
        print(f"❌ Error during message cleanup: {e}")

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
    try:
        synced = await bot.tree.sync()
        print(f"🔃 Synced {len(synced)} command(s)")
        await cleanup_old_messages()
        bot.add_view(FiveManView(0))  # Dummy creator_id for registration only
        print(f"✅ Logged in as {bot.user}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

bot.run(discord_token)