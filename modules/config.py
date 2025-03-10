import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_NAME = os.getenv("DB_NAME", "filings.db")  # Provide a default fallback if not found
USE_DATE_FILTER = os.getenv("USE_DATE_FILTER", "False").lower() == "true"
DATE_FILTER_DAYS = int(os.getenv("DATE_FILTER_DAYS", "7"))
PROXY = os.getenv("PROXY")