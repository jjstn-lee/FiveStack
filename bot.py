import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from bot import FiveStack
from config import *

import bot
import config

# ...
# dictionary to track active groups per guild
# active_groups = {}  # guild_id hashes to the appropriate FiveManView

# group = discord.app_commands.Group(name="5stack", description="Commands for FiveStack")




# class to represent form that user submits to show availability (discord.Modal)


# def get_guild_active_group(guild_id: int) -> FiveManView:
#     """Get the active group for a specific guild"""
#     return active_groups.get(guild_id)

# def set_guild_active_group(guild_id: int, group: FiveManView):
#     """Set the active group for a specific guild"""
#     active_groups[guild_id] = group

# def clear_guild_active_group(guild_id: int):
#     """Clear the active group for a specific guild"""
#     if guild_id in active_groups:
#         del active_groups[guild_id]


# @group.command(name="debug_all_sessions", description="Show all active sessions across all guilds (debug)")
# async def debug_all_sessions(interaction: discord.Interaction):
#     """Debug command to show all active sessions"""
#     if not active_groups:
#         await interaction.response.send_message("📊 No active sessions found in any guild.", ephemeral=True)
#         return
    
#     message_parts = ["📊 **All Active Sessions:**\n"]
#     for guild_id, group in active_groups.items():
#         guild = bot.get_guild(guild_id)
#         guild_name = guild.name if guild else f"Unknown Guild ({guild_id})"
#         filled_count = sum(1 for slot in group.slots if slot)
#         session_age = int((time.time() - group.created_at) / 60)
        
#         message_parts.append(
#             f"• **{guild_name}**: {filled_count}/5 members, {session_age} min old, "
#             f"Creator: <@{group.creator_id}>, Closed: {'Yes' if group.is_closed else 'No'}"
#         )
    
#     await interaction.response.send_message("\n".join(message_parts), ephemeral=True)






async def main():
    # Load all Cogs
    bot = FiveStack()

    # Optionally add your FiveStack Cog directly if not in ./cogs
    # await bot.add_cog(FiveStack(bot))

    # Run the bot
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    # Run the bot asynchronously
    asyncio.run(main())