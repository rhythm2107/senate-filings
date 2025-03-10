import time
from modules.scraper_filings import scrape_filings
from modules.scraper_transactions import scrape_transactions
from modules.notify_system import send_unnotified_discord_notifications
from modules.logger import setup_logger

# Create a logger object for debugging purposes
logger = setup_logger("main_logger", "main.log")

def main():
    scrape_filings()
    time.sleep(2)

    scrape_transactions()
    time.sleep(2)

    send_unnotified_discord_notifications()
    time.sleep(2)

if __name__ == "__main__":
    main()