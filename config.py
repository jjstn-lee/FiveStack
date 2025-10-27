import os
import discord
from dotenv import load_dotenv

# handle .env file
load_dotenv()
app_id = os.getenv("APP_ID")
discord_token = os.getenv("DISCORD_TOKEN")
public_key = os.getenv("PUBLIC_KEY")

# determine which environment to use
ENVIRONMENT = os.getenv("BOT_ENV", "dev").lower()  # default to 'dev'

if ENVIRONMENT == "prod":
    DISCORD_TOKEN = os.getenv("PROD_DISCORD_TOKEN")
else:
    DISCORD_TOKEN = os.getenv("DEV_DISCORD_TOKEN")

# Bot intents configuration
intents = discord.Intents.default()
intents.message_content = False
intents.guilds = True
intents.members = True

# Bot configuration
BOT_COMMAND_PREFIX = "/"