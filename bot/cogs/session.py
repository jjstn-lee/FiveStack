import time
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from bot import FiveStack, get_bot
from models.FiveManView import FiveManView
import config


class Session(commands.Cog):
    
    
    
    # Define the slash command group as a class attribute
    session_group = app_commands.Group(
        name=("5stack" if config.BOT_ENV == "prod" else "5test"),
        description="Commands for FiveStack",
    )
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.instance = get_bot()

    @session_group.command(name="session-status", description="Check current session status")
    async def session_status(self, interaction: discord.Interaction):
        """Debug command to check session status"""
        guild_id = interaction.guild_id
        current_active_group = self.instance.active_groups.get(guild_id)
        
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

    @session_group.command(name="fivestack", description="Start a five stack!")
    async def five_man_command_impl(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        try:
            # Check if there's already an active group in this guild
            current_active_group = self.instance.active_groups.get(guild_id)
            if current_active_group and not current_active_group.is_closed:
                await interaction.response.send_message(
                    "❌ There's already an active five stack in this server! Only one group can be active at a time.\n"
                    "Close the group that is open first.",
                    ephemeral=True
                )
                return
            
            # RESPOND IMMEDIATELY - nothing before this line should be slow
            await interaction.response.send_message("⏳ Creating your FiveStack group...", ephemeral=True)
            
            # Now do the slower operations
            view = FiveManView(creator_id=interaction.user.id, guild_id=guild_id)
            self.instance.active_groups[guild_id] = view
            
            embed = view.update_embed()
            
            # Add persistent view to bot
            self.bot.add_view(view)
            
            # Find role
            role = discord.utils.get(interaction.guild.roles, name="league-of-legends")
            ping = role.mention if role else ""
            
            # Send FiveStack message
            channel = interaction.channel
            fivestack_message = await channel.send(
                content=f"{ping} – New FiveStack group forming! 🎮",
                embed=embed,
                view=view
            )
            
            # Store the message reference
            view.original_message = fivestack_message
            
            # Update the ephemeral response
            await interaction.edit_original_response(content="✅ FiveStack created successfully!")
            
        except Exception as e:
            print(f"Error in fivestack command: {e}")
            import traceback
            traceback.print_exc()  # This will show the full error
            
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Failed to create fivestack. Please try again.", ephemeral=True)
            else:
                # If already responded, use edit
                await interaction.edit_original_response(content="❌ Failed to create fivestack. Please try again.")

    @session_group.command(name="reset-fivestack", description="Reset the bot for this guild (clears active FiveStack group)")
    async def reset_guild_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        try:
            # Check if there's an active group
            if guild_id not in self.instance.active_groups:
                await interaction.response.send_message(
                    "ℹ️ No active FiveStack group found for this guild. Nothing to reset.",
                    ephemeral=True
                )
                return
            
            current_group = self.instance.active_groups[guild_id]
            
            if hasattr(current_group, 'is_closed'):
                current_group.is_closed = True
            
            # Stop view to prevent further interactions
            if hasattr(current_group, 'stop'):
                current_group.stop()
            
            # Disable the original message's view (if message reference exists)
            if hasattr(current_group, 'original_message') and current_group.original_message:
                try:
                    await current_group.original_message.edit(
                        content=f"{current_group.original_message.content}\n\n❌ **This FiveStack has been reset by an administrator.**",
                        view=None  # Remove the view entirely
                    )
                except discord.NotFound:  # Message was deleted, OK
                    pass
                except discord.Forbidden:  # Bot doesn't have permission to edit, OK
                    pass
            
            # Remove from active groups
            del self.instance.active_groups[guild_id]
            await interaction.response.send_message(
                f"✅ **Guild FiveStack reset successfully!**\n"
                f"The active group has been cleared and you can now create a new FiveStack.",
                ephemeral=True
            )
            print(f"Guild {guild_id} FiveStack reset by user {interaction.user.id} ({interaction.user.display_name})")
            
        except KeyError:
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

    @session_group.command(name="cleanup-messages", description="Delete all old FiveStack messages (requires manage messages permission)")
    async def cleanup_command(self, interaction: discord.Interaction):
        """Manual cleanup command for slash command interface"""
        await interaction.response.defer(ephemeral=True)  # Defer response because it might take a long time    
        try:
            deleted_total = 0
            guild = interaction.guild
            # Loop through all channels the bot can see in this guild
            for channel in guild.text_channels:
                # Check if bot has permission to read message history and delete messages
                permissions = channel.permissions_for(guild.me)
                if not (permissions.read_message_history and permissions.manage_messages):
                    continue
                try:
                    deleted_count = 0
                    async for message in channel.history(limit=20): 
                        if message.author == self.bot.user:
                            try:
                                await message.delete()
                                deleted_count += 1
                                # Add delay between deletions to avoid rate limiting
                                await asyncio.sleep(0.5)  # 500ms delay between deletions
                            except discord.NotFound:  # Message already deleted
                                pass
                            except discord.Forbidden:  # Lost permissions mid-cleanup
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
                        
                except discord.Forbidden:  # No permissions to read this channel
                    continue
                except Exception as e:
                    print(f"❌ Error cleaning up #{channel.name} in {guild.name}: {e}")
            
            # Send appropriate follow ups
            if deleted_total > 0:
                await interaction.followup.send(f"🧹 Total cleanup: {deleted_total} message(s) deleted from this server")
            else:
                await interaction.followup.send("✅ No old bot messages found to clean up in this server")
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error during message cleanup: {e}")


# Setup function to allow load_extension
async def setup(bot: commands.Bot):
    cog = Session(bot)
    await bot.add_cog(cog)
    # Register the group with its subcommands
    if not any(cmd.name == cog.session_group.name for cmd in bot.tree.get_commands()):
        bot.tree.add_command(cog.session_group)