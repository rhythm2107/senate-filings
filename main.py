import time
from modules.scraper_filings import scrape_filings
from modules.scraper_transactions import scrape_transactions
from modules.notify_system import send_unnotified_discord_notifications
from modules.logger import setup_logger
from modules.db_helper import init_db, init_analytics_table
from modules.config import DB_NAME
from modules.analytics_txmatch import process_transactions_analytics
from modules.analytics_senators import update_senators_analytics
from modules.analytics_party import update_party_analytics

# Create a logger object for debugging purposes
logger = setup_logger("main_logger", "main.log")
logger_analytics = setup_logger("analytics", "analytics.log")

def main():
    # logger.info("[MAIN] Starting scrape_filings")
    # scrape_filings()
    # time.sleep(2)

    # logger.info("[MAIN] Starting scrape_transactions")
    # scrape_transactions()
    # time.sleep(2)

    conn = init_db("filings.db") # Rename to DB_NAME constant later after debugging is finished

    logger.info("[MAIN] Starting process_transactions_analytics")
    process_transactions_analytics(conn)
    time.sleep(2)

    logger.info("[MAIN] Starting update_senators_analytics")
    update_senators_analytics(conn)
    time.sleep(2)
    
    logger.info("[MAIN] Starting update_party_analytics")
    update_party_analytics(conn)
    time.sleep(2)

    # logger.info("[MAIN] Starting send_unnotified_discord_notifications")
    # send_unnotified_discord_notifications()
    # time.sleep(2)

if __name__ == "__main__":
    main()