import discord
from discord.ext import commands

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

class FiveManView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=3600)  # auto-timeout after 1 hour
        self.slots = [None] * 5  # 5 slots, initially empty

        for i in range(5):
            self.add_item(SlotButton(slot_index=i, label=f"Join Slot {i + 1}"))

    def is_user_already_joined(self, user: discord.User):
        return user.id in [s["user"].id for s in self.slots if s]

    def update_embed(self):
        embed = discord.Embed(title="🧩 5man Group Finder", color=discord.Color.blurple())
        for i, slot in enumerate(self.slots):
            if slot:
                embed.add_field(name=f"Slot {i+1}", value=f"{slot['user'].mention} at {slot['time'] or 'No time set'}", inline=False)
            else:
                embed.add_field(name=f"Slot {i+1}", value="🔲 Open Slot", inline=False)
        return embed


class SlotButton(discord.ui.Button):
    def __init__(self, slot_index, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.slot_index = slot_index

    async def callback(self, interaction: discord.Interaction):
        view: FiveManView = self.view

        if view.slots[self.slot_index]:
            await interaction.response.send_message("❌ This slot is already filled.", ephemeral=True)
            return

        if view.is_user_already_joined(interaction.user):
            await interaction.response.send_message("❗ You already joined another slot.", ephemeral=True)
            return

        # Ask user for optional time input
        await interaction.response.send_modal(
            TimeModal(
                slot_index=self.slot_index,
                user=interaction.user,
                view=view,  # `view` is available from `self.view`
                message=view.original_message
            )
        )



class TimeModal(discord.ui.Modal, title="Enter Time (Optional)"):
    time_input = discord.ui.TextInput(
        label="When are you available?",
        required=False,
        placeholder="e.g. 7 PM EST"
    )

    def __init__(self, slot_index, user, view, message):
        super().__init__()
        self.slot_index = slot_index
        self.user = user
        self.view_ref = view
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        self.view_ref.slots[self.slot_index] = {
            "user": self.user,
            "time": self.time_input.value.strip() if self.time_input.value else None
        }

        embed = self.view_ref.update_embed()
        await self.message.edit(embed=embed, view=self.view_ref)
        # await interaction.response.send_message("✅ Slot filled!", ephemeral=True)




@bot.tree.command(name="5man", description="Start a 5-man party finder")
async def five_man_command(interaction: discord.Interaction):
    view = FiveManView()
    embed = view.update_embed()

    role = discord.utils.get(interaction.guild.roles, name="league-of-legends")
    ping = role.mention if role else "league-of-legends"


    # ⬇️ Important: save the bot message we send
    message = await interaction.response.send_message(
        content=f"{ping} – New 5man group forming!",
        embed=embed,
        view=view
    )

    # If using followup, store this:
    view.original_message = await interaction.original_response()



@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔃 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

bot.run(discord_token)
