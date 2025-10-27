import time
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from bot import get_guild_active_group, active_groups, bot, FiveManView, set_guild_active_group

class Session(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    session_group = app_commands.Group(
        name="session",
        description="Commands related to sessions"
    )

    @session_group.command(name="status", description="Check current session status")
    async def session_status(self, interaction: discord.Interaction):
        """Debug command to check session status"""
        guild_id = interaction.guild_id
        current_active_group = get_guild_active_group(guild_id)
        
        if current_active_group:
            filled_count = sum(1 for slot in current_active_group.slots if slot)
            session_age = time.time() - current_active_group.created_at
            session_minutes = int(session_age / 60)
            last_refresh_age = int((time.time() - current_active_group.last_refresh) / 60)
            
            await interaction.response.send_message(
                f"📊 **Session Status for {interaction.guild.name}:**\n"
                f"• Active group: Yes\n"
                f"• Members: {filled_count}/5\n"
                f"• Age: {session_minutes} minutes\n"
                f"• Last refresh: {last_refresh_age} minutes ago\n"
                f"• Creator: <@{current_active_group.creator_id}>\n"
                f"• Closed: {'Yes' if current_active_group.is_closed else 'No'}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"📊 No active session found for {interaction.guild.name}.", 
                ephemeral=True
            )

    @session_group.command(name="start", description="Start a five stack!")
    async def five_man_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        try:
            # DEBUG

            # check if there's already an active group in this guild
            current_active_group = get_guild_active_group(guild_id)
            if current_active_group and not current_active_group.is_closed:
                await interaction.response.send_message(
                    "❌ There's already an active five stack in this server! Only one group can be active at a time.\n"
                    "Close the group that is open first.",
                    ephemeral=True
                )
                return
            
            # acknowledge (discord requires you acknowledge an interaction within 3 secs)
            await interaction.response.send_message("⏳ Creating your FiveStack group...", ephemeral=True)
            
            # create new group with guild_id
            view = FiveManView(creator_id=interaction.user.id, guild_id=guild_id)
            set_guild_active_group(guild_id, view)  # Set as the active group for this guild
            
            embed = view.update_embed()
            
            # Debug prints
            print(f"=== DEBUG FIVESTACK CREATION ===")
            print(f"View created: {view}")
            print(f"Embed created: {embed}")
            print(f"Embed title: {embed.title if embed else 'No embed'}")
            print(f"View children: {len(view.children) if hasattr(view, 'children') else 'No children attr'}")
            if hasattr(view, 'children'):
                for i, child in enumerate(view.children):
                    print(f"  Child {i}: {type(child).__name__} - {getattr(child, 'label', 'No label')}")
            
            bot.add_view(view)
            
            # if able to find role, ping people with that role
            role = discord.utils.get(interaction.guild.roles, name="league-of-legends")
            ping = role.mention if role else ""
            
            # send FiveStack message as message (NOT INTERACTION! important for clean-up) to the channel
            channel = interaction.channel
            
            # More debug info before sending
            print(f"About to send message to channel: {channel}")
            print(f"Content: {ping} – New FiveStack group forming! 🎮")
            print(f"Embed is None: {embed is None}")
            print(f"View is None: {view is None}")
            
            fivestack_message = await channel.send(
                content=f"{ping} – New FiveStack group forming! 🎮",
                embed=embed,
                view=view
            )
            
            print(f"Message sent successfully: {fivestack_message.id}")
            
            # store the message reference
            view.original_message = fivestack_message
            
            # update the ephemeral response to confirm success
            await interaction.edit_original_response(content="✅ FiveStack created successfully!")
            
        except Exception as e:
            print(f"Error in 5stack command: {e}")
            import traceback
            traceback.print_exc()  # This will show the full error
            
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Failed to create 5 man. Please try again.", ephemeral=True)
            else:
                # if already responded, use edit
                await interaction.edit_original_response(content="❌ Failed to create 5 man. Please try again.")

    @session_group.command(name="reset", description="Reset the bot for this guild (clears active FiveStack group)")
    async def reset_guild_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        try:
            # check if there's an active group
            if guild_id not in active_groups:
                await interaction.response.send_message(
                    "ℹ️ No active FiveStack group found for this guild. Nothing to reset.",
                    ephemeral=True
                )
                return
            
            current_group = active_groups[guild_id]
            
            if hasattr(current_group, 'is_closed'):
                current_group.is_closed = True
            
            # stop view to prevent further interactions
            if hasattr(current_group, 'stop'):
                current_group.stop()
            
            # disable the original message's view (if message reference exists)
            if hasattr(current_group, 'original_message') and current_group.original_message:
                try:
                    await current_group.original_message.edit(
                        content=f"{current_group.original_message.content}\n\n❌ **This FiveStack has been reset by an administrator.**",
                        view=None  # Remove the view entirely
                    )
                except discord.NotFound: # message was deleted, OK
                    pass
                except discord.Forbidden: # bot doesn't have permission to edit, OK
                    pass
            
            # remove from active groups
            del active_groups[guild_id]
            await interaction.response.send_message(
                f"✅ **Guild FiveStack reset successfully!**\n"
                f"The active group has been cleared and you can now create a new FiveStack.",
                ephemeral=True
            )
            print(f"Guild {guild_id} FiveStack reset by user {interaction.user.id} ({interaction.user.display_name})")
            
        except KeyError:
            # don't think this will ever happen but just in case?
            await interaction.response.send_message(
                "ℹ️ No active FiveStack group found for this guild.",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in reset command: {e}")
            import traceback
            traceback.print_exc()
            
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while resetting the guild. Please try again.",
                    ephemeral=True
                )

    @session_group.command(name="cleanup", description="Delete all old FiveStack messages (requires read and manage messages permissions)")
    async def cleanup_command(self, interaction: discord.Interaction):
        """Manual cleanup command for slash command interface"""
        await interaction.response.defer(ephemeral=True)  # defer response because it might take a long time    
        try:
            deleted_total = 0
            guild = interaction.guild
            # loop through all channels the bot can see in this guild
            for channel in guild.text_channels:
                # check if bot has permission to read message history and delete messages
                permissions = channel.permissions_for(guild.me)
                if not (permissions.read_message_history and permissions.manage_messages):
                    continue
                try:
                    deleted_count = 0
                    async for message in channel.history(limit=20): 
                        if message.author == bot.user:
                            try:
                                await message.delete()
                                deleted_count += 1
                                # add delay between deletions to avoid rate limiting
                                await asyncio.sleep(0.5)  # 500ms delay between deletions
                            except discord.NotFound: # message already deleted
                                pass
                            except discord.Forbidden: # lost permissions mid-cleanup
                                break
                            except discord.HTTPException as e:
                                if e.status == 429:  # rate limited
                                    print(f"⏳ Rate limited, waiting...")
                                    await asyncio.sleep(2)  # wait 2 seconds on rate limit
                                    continue
                                else:
                                    raise
                    
                    if deleted_count > 0:
                        print(f"🧹 Cleaned up {deleted_count} old bot message(s) from #{channel.name} in {guild.name}")
                        deleted_total += deleted_count
                    
                    # add delay between channels
                    if deleted_count > 0:
                        await asyncio.sleep(1)  # 1 second delay between channels that had deletions
                        
                except discord.Forbidden: # no permissions to read this channel
                    continue
                except Exception as e:
                    print(f"❌ Error cleaning up #{channel.name} in {guild.name}: {e}")
            
            # send appropriate follow ups
            if deleted_total > 0:
                await interaction.followup.send(f"🧹 Total cleanup: {deleted_total} message(s) deleted from this server")
            else:
                await interaction.followup.send("✅ No old bot messages found to clean up in this server")
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error during message cleanup: {e}")

# Setup function to allow load_extension
async def setup(bot: commands.Bot):
    await bot.add_cog(Session(bot))
