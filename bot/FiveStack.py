import os
import discord

from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dotenv import load_dotenv

from bot.cogs import *
import config
from models import FiveManView

print(config.BOT_ENV)
print(config.APP_ID)
print(config.PUBLIC_KEY)
print(config.DISCORD_TOKEN)

class FiveStack:
    def __init__(self):
        # Don't create group here - let the cog handle it
        self.active_groups = {}
        self.bot = commands.Bot(command_prefix="!", intents=config.intents)
        self.setup_bot_events()
        print("initialized FiveStack class, now need to load cogs")

    async def load_cogs(self):
        for filename in os.listdir("./bot/cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                extension = f"bot.cogs.{filename[:-3]}"
                try:
                    await self.bot.load_extension(extension)
                    print(f"✅ Loaded {extension}")
                    
                    # Get the Cog instance
                    cog_name = filename[:-3].capitalize()
                    cog_instance = self.bot.get_cog(cog_name)
                    
                    if cog_instance:
                        print(f"📋 Cog '{cog_instance.qualified_name}' loaded:")
                        
                        # Check for traditional prefix commands
                        prefix_commands = cog_instance.get_commands()
                        if prefix_commands:
                            print(f"  Prefix commands:")
                            for cmd in prefix_commands:
                                print(f"   - {cmd.name}")
                        
                        # Check for app command groups
                        if hasattr(cog_instance, 'session_group'):
                            print(f"  App command group: /{cog_instance.session_group.name}")
                            for cmd in cog_instance.session_group.commands:
                                print(f"   - /{cog_instance.session_group.name} {cmd.name}")
                        
                        # Check for standalone app commands
                        app_commands = cog_instance.get_app_commands()
                        if app_commands:
                            print(f"  Standalone app commands:")
                            for cmd in app_commands:
                                print(f"   - /{cmd.name}")
                                
                    else:
                        print(f"⚠️ Cog instance '{cog_name}' not found in bot.")
                        
                except Exception as e:
                    print(f"❌ Failed to load {extension}: {e}")
                    import traceback
                    traceback.print_exc()

    def setup_bot_events(self):
        @self.bot.event
        async def on_ready():
            try:
                synced = await self.bot.tree.sync()
                print(f"🔃 Synced {len(synced)} command(s)")
                for cmd in synced:
                    print(f"  - {cmd.name} ({cmd.type})")
                # self.bot.add_view(FiveManView(0, 0))
                print(f"✅ Logged in as {self.bot.user}")
            except Exception as e:
                print(f"❌ Error syncing commands: {e}")
                import traceback
                traceback.print_exc()