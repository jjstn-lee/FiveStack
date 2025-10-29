import os
import discord
from dotenv import load_dotenv

# handle .env file
load_dotenv()

# determine which environment to use
BOT_ENV = os.getenv("BOT_ENV", "dev").lower()  # default to 'dev'

if BOT_ENV == "prod":
    APP_ID = os.getenv("PROD_APP_ID")
    PUBLIC_KEY = os.getenv("PROD_PUBLIC_KEY")
    DISCORD_TOKEN = os.getenv("PROD_DISCORD_TOKEN")
else:
    APP_ID = os.getenv("DEV_APP_ID")
    PUBLIC_KEY = os.getenv("DEV_PUBLIC_KEY")
    DISCORD_TOKEN = os.getenv("DEV_DISCORD_TOKEN")

# Bot intents configuration
intents = discord.Intents.default()
intents.message_content = False
intents.guilds = True
intents.members = True

# Bot configuration
BOT_COMMAND_PREFIX = "/"