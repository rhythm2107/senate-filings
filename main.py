import time
from modules.scraper_filings import scrape_filings
from modules.scraper_transactions import scrape_transactions
from modules.notify_system import send_unnotified_discord_notifications
from modules.logger import setup_logger
from modules.db_helper import init_db, init_analytics_table
from modules.analytics import update_analytics
from modules.config import DB_NAME

# Create a logger object for debugging purposes
logger = setup_logger("main_logger", "main.log")

# def main():
#     # logger.info("[MAIN] Starting scrape_filings")
#     # scrape_filings()
#     # time.sleep(2)

#     # logger.info("{MAIN] Starting scrape_transactions")
#     # scrape_transactions()
#     # time.sleep(2)

#     logger.info("{MAIN] Starting send_unnotified_discord_notifications")
#     send_unnotified_discord_notifications()
#     time.sleep(2)

# def main():
#     conn = init_db(DB_NAME)
#     init_analytics_table(conn)
#     update_analytics(conn)
#     print("Analytics table updated.")
#     conn.close()

# if __name__ == "__main__":
#     main()

import sqlite3
from modules.config import DB_NAME
from modules.db_helper import init_db
from modules.analytics import init_analytics_table, update_analytics

def main():
    # Connect to your database
    conn = init_db(DB_NAME)
    
    # Ensure the analytics table exists
    init_analytics_table(conn)
    
    # Update the analytics table with aggregated metrics
    update_analytics(conn)
    
    # Optionally, fetch and print the analytics table contents to verify
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analytics")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    conn.close()

if __name__ == '__main__':
    main()
