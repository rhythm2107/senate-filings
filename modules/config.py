import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

DISCORD_WEBHOOK_NOTIFICATION_FREE = os.getenv("DISCORD_WEBHOOK_NOTIFICATION_FREE")
DISCORD_WEBHOOK_NOTIFICATION_OTHER = os.getenv("DISCORD_WEBHOOK_NOTIFICATION_OTHER")
DISCORD_WEBHOOK_NOTIFICATION_LARGE = os.getenv("DISCORD_WEBHOOK_NOTIFICATION_LARGE")
DISCORD_WEBHOOK_NOTIFICATION_STOCK = os.getenv("DISCORD_WEBHOOK_NOTIFICATION_STOCK")
DISCORD_WEBHOOK_DEBUG = os.getenv("DISCORD_WEBHOOK_DEBUG")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_BOT_CMD_PREFIX = os.getenv("DISCORD_BOT_CMD_PREFIX", "!")
DISCORD_BOT_GUILD_ID = int(os.getenv("DISCORD_BOT_GUILD_ID"))
DISCORD_BOT_DEV_CHANNEL_ID = int(os.getenv("DISCORD_BOT_DEV_CHANNEL_ID"))
DISCORD_BOT_CMD_CHANNEL_ID = int(os.getenv("DISCORD_BOT_CMD_CHANNEL_ID"))
SUBSCRIBE_VIP_ROLE_ID = int(os.getenv("SUBSCRIBE_VIP_ROLE_ID"))
SUBSCRIBE_LIFETIME_ROLE_ID = int(os.getenv("SUBSCRIBE_LIFETIME_ROLE_ID"))
SUBSCRIBE_INFO_CHANNEL_ID = int(os.getenv("SUBSCRIBE_INFO_CHANNEL_ID"))
SCRIPT_FREQUENCY_SECONDS = int(os.getenv("SCRIPT_FREQUENCY_SECONDS"))
MINIMUM_STOCK_TRANSACTIONS = int(os.getenv("MINIMUM_STOCK_TRANSACTIONS"))
KOFI_SHOP_STORE_LINK = os.getenv("KOFI_SHOP_STORE_LINK")
DB_NAME = os.getenv("DB_NAME", "filings.db")  # Provide a default fallback if not found
USE_DATE_FILTER = os.getenv("USE_DATE_FILTER", "False").lower() == "true"
DATE_FILTER_DAYS = int(os.getenv("DATE_FILTER_DAYS", "7"))
PROXY = os.getenv("PROXY")

# Retrieve the environment variables for allowed roles
allowed_role_ids_str = os.getenv("ALLOWED_ROLE_IDS", "")
ALLOWED_ROLE_IDS = {int(role_id.strip()) for role_id in allowed_role_ids_str.split(",") if role_id.strip()}