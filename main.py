from modules.scraper_filings import scrape_filings
from modules.scraper_transactions import scrape_transactions
from modules.notify_system import send_unnotified_discord_notifications
from modules.logger import setup_logger

# Create a logger object for debugging purposes
logger = setup_logger("main_logger", "main.log")

