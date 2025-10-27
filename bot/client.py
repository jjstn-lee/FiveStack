import discord

from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dotenv import load_dotenv

from cogs import *
from config import *
from models import FiveManView

class FiveStack:
    async def load_cogs(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                extension = f"cogs.{filename[:-3]}"
                await self.load_extension(extension)
                print(f"Loaded {extension}")

    
    def __init__(self):
        group = discord.app_commands.Group(name="5stack", description="Commands for FiveStack")
        bot = commands.Bot(command_prefix="!", intents=intents)
        bot.tree.add_command(group)
        self.load_cogs(self)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.content.startswith("/"):
            try:
                await message.delete()
            except:
                pass

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            synced = await self.bot.tree.sync()
            print(f"🔃 Synced {len(synced)} command(s)")
            self.bot.add_view(FiveManView(0, 0))
            print(f"✅ Logged in as {self.bot.user}")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")
    
