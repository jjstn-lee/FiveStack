
import time
import discord

import bot
from ui import SlotButton
from ui import ResetButton
from ui import LeaveButton
from ui import CloseButton


class FiveManView(discord.ui.View):
    def __init__(self, creator_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.guild_id = guild_id
        self.original_message = None
        self.is_closed = False
        self.created_at = time.time()
        self.last_refresh = time.time()
        
        self.slots = [None] * 5
        self.add_item(SlotButton())
        self.add_item(ResetButton())
        self.add_item(LeaveButton())
        self.add_item(CloseButton())
    
    # function to mark group as closed and clear guild reference
    def close_group(self):
        global active_groups
        self.is_closed = True
        if self.guild_id in active_groups and active_groups[self.guild_id] == self:
            del active_groups[self.guild_id]
    
    def is_user_already_joined(self, user: discord.User):
        return any(slot and slot["user_id"] == user.id for slot in self.slots if slot)
    
    def get_user_slot(self, user: discord.User):
        for i, slot in enumerate(self.slots):
            if slot and slot["user_id"] == user.id:
                return i
        return None
    
    # return index of the first empty slot, or none if full
    def get_first_available_slot(self):
        for i, slot in enumerate(self.slots):
            if slot is None:
                return i
        return None
    
    def is_full(self):
        return all(slot is not None for slot in self.slots)
    
    def update_embed(self):
        filled_count = sum(1 for slot in self.slots if slot)
        remaining_count = 5 - filled_count
        
        progress_bar = ""
        for i in range(5):
            if i < filled_count:
                progress_bar += "✅"
            else:
                progress_bar += "⬜"
        
        if self.is_full():
            color = discord.Color.green()
            title = f"🎉 5 MAN GROUP - FULL! {progress_bar} {filled_count}/5"
        else:
            color = discord.Color.blurple()
            title = f"🧩 5 MAN PROGRESS: {progress_bar} {filled_count}/5"
        embed = discord.Embed(title=title, color=color)
        
        description = ""
        filled_slots = [slot for slot in self.slots if slot]
        if filled_slots:
            description += "**Joined Players:**\n"
            for slot in filled_slots:
                # try to get user mention; if not found, fallback to username
                try:
                    user = bot.get_user(slot["user_id"])
                    user_mention = user.mention if user else f"<@{slot['user_id']}>"
                except:
                    user_mention = slot.get("username", f"<@{slot['user_id']}>")
                
                # include emoji if found, else don't show emoji
                role_text = ""
                if slot.get("role"):
                    role_emoji_ids = {
                        "Top": "<:top_lane:1403834039735025674>",
                        "Jungle": "<:jungle:1403834034957713691>", 
                        "Mid": "<:mid_lane:1403834037776154785>",
                        "ADC": "<:bot_lane:1403834041010098246>",
                        "Support": "<:support:1403834038694973521>",
                        "Fill": "<:fill:1403834036866125884>",
                    }
                    
                    role_emoji = ""
                    emoji_name = role_emoji_ids.get(slot["role"])
                    if emoji_name:
                        guild = bot.get_guild(self.guild_id)
                        if guild:
                            emoji = discord.utils.get(guild.emojis, name=emoji_name)
                            if emoji:
                                role_emoji = str(emoji) + " "
                    role_text = f" **{role_emoji}{slot['role']}**"
                time_text = f" - *{slot['time']}*" if slot['time'] else ""
                description += f"• {user_mention}{role_text}{time_text}\n"
            description += "\n"
        
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
        
        return embed