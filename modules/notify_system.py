import requests
import sqlite3
import datetime
import time
from modules.config import DISCORD_WEBHOOK_URL, DB_NAME

# --- Database Setup Functions ---

def init_notification_log(conn):
    """
    Create a notification_log table if it doesn't already exist.
    This table stores records of sent notifications using the composite key (ptr_id, transaction_number).
    """
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notification_log (
            ptr_id TEXT,
            transaction_number INTEGER,
            notified_at TEXT,
            status_code INTEGER,
            error_message TEXT,
            PRIMARY KEY (ptr_id, transaction_number)
        )
    ''')
    conn.commit()

def get_unnotified_transactions(conn):
    """
    Retrieve transactions (with joined filing data) that have not yet been notified.
    This uses a subquery to ensure that only transactions not present in the notification_log are returned.
    Returns a list of tuples with the following order:
        (ptr_id, transaction_number, transaction_date, owner, ticker,
         asset_name, additional_info, asset_type, type, amount, comment, filing_date, name)
    """
    c = conn.cursor()
    query = '''
        SELECT t.ptr_id, t.transaction_number, t.transaction_date, t.owner, t.ticker, 
               t.asset_name, t.additional_info, t.asset_type, t.type, t.amount, t.comment,
               f.filing_date,
               f.first_name || ' ' || f.last_name AS name
        FROM transactions t
        JOIN filings f ON t.ptr_id = f.ptr_id
        WHERE NOT EXISTS (
            SELECT 1 FROM notification_log n
            WHERE n.ptr_id = t.ptr_id AND n.transaction_number = t.transaction_number
        )
        ORDER BY f.filing_date DESC, t.transaction_date DESC;
    '''
    c.execute(query)
    return c.fetchall()


def log_notification(conn, ptr_id, transaction_number, notified_at, status_code, error_message=""):
    """
    Insert a record into the notification_log table indicating that a notification for this transaction was attempted.
    """
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO notification_log (ptr_id, transaction_number, notified_at, status_code, error_message)
        VALUES (?, ?, ?, ?, ?)
    ''', (ptr_id, transaction_number, notified_at, status_code, error_message))
    conn.commit()

# --- Notification Function ---

def send_discord_notification(transaction):
    """
    Send a Discord notification using an embed.
    
    The transaction tuple is expected to contain:
      (ptr_id, transaction_number, transaction_date, owner, ticker,
       asset_name, additional_info, asset_type, txn_type, amount, comment, filing_date)
    """
    (ptr_id, txn_num, txn_date, owner, ticker, asset_name,
     additional_info, asset_type, txn_type, amount, comment, filing_date, name) = transaction

    # Set left border color
    color = 3447003
    if ticker == '--':
        color = 3462032

    # Build an embed payload
    embed = {
        "title": f"Senator {name}",
        "description": (
            f"A new transaction from Senator {name}!\n"
            f"For detailed analytics, please <#1348693301607530526> to our <@&1348695007778967614> role.\n"
        ),
        "color": color,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "footer": {
            "icon_url": "https://i.imgur.com/J01MSXf.jpeg",
            "text": "House of Data"
        },
        "thumbnail": {
            "url": "https://i.imgur.com/J01MSXf.jpeg"
        },
        "fields": [
            {"name": "Ticker", "value": ticker, "inline": False},
            {"name": "Owner", "value": owner, "inline": False},
            {"name": "Asset Name", "value": asset_name, "inline": True},
            {"name": "Asset Type", "value": asset_type, "inline": True},
            {"name": "Transaction Type", "value": txn_type, "inline": True},
            {"name": "Amount", "value": amount, "inline": True},
            {"name": "Filing Date", "value": filing_date, "inline": True},
            {"name": "Transaction Date", "value": txn_date, "inline": True}
        ]
    }

    payload = {
        "content": None,
        "embeds": [embed],
        "attachments": [],
        # This ensures that even though the embed text displays the role mention,
        # no ping/notification is actually sent to that role.
        "allowed_mentions": {
            "roles": []
        }
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    return response


if __name__ == "__main__":
    # Example transaction tuple:
    sample_transaction_1 = (
        "41868f55-ad42-4855-9aca-1764a05fb956",  # ptr_id
        4,                                      # Transaction Number
        "12/22/2021",                           # Transaction Date
        "Spouse",                               # Owner
        "--",                                   # Ticker
        "JPM Contingent Autocall on Gilead",          # Asset Name
        "Rate/Coupon: 8.65% Matures: 09/20/2024",   # Additional Info
        "Corporate Bond",                       # Asset Type
        "Sale (Full)",                          # Type
        "$15,001 - $50,000",                      # Amount
        "--",                                   # Comment
        "01/04/2022",                            # Filing Date
        "Thomas R Carper",                            # Filing Date
    )

    sample_transaction_2 = (
        "8d87d0d9-8094-4891-a29c-c0e0435acb1a",  # ptr_id
        24,                                      # Transaction Number
        "02/14/2020",                           # Transaction Date
        "Joint",                               # Owner
        "XOM",                                   # Ticker
        "Exxon Mobil Corporation",          # Asset Name
        "",   # Additional Info
        "Stock",                       # Asset Type
        "Sale (Full)",                          # Type
        "$250,001 - $500,000",                      # Amount
        "--",                                   # Comment
        "05/01/2020",                            # Filing Date
        "Kelly Loeffler",                            # Filing Date
    )

    sample_transaction_3 = (
        "41868f55-ad42-4855-9aca-1764a05fb956",  # ptr_id
        4,                                      # Transaction Number
        "12/22/2021",                           # Transaction Date
        "Spouse",                               # Owner
        "--",                                   # Ticker
        "JPM Contingent Autocall on Gilead",          # Asset Name
        "Rate/Coupon: 8.65% Matures: 09/20/2024",   # Additional Info
        "Corporate Bond",                       # Asset Type
        "Sale (Full)",                          # Type
        "$15,001 - $50,000",                      # Amount
        "--",                                   # Comment
        "01/04/2022",                            # Filing Date
        "xd",                            # Filing Date
    )
    # send_discord_notification(sample_transaction_1)

# --- Main Process ---

def send_discord_notifications():
    # Open the database connection
    conn = sqlite3.connect(DB_NAME)
    init_notification_log(conn)
    
    # Retrieve transactions that haven't been notified yet.
    unnotified_transactions = get_unnotified_transactions(conn)
    print(f"Found {len(unnotified_transactions)} unnotified transactions.")
    
    total_new_notifications = 0
    for transaction in unnotified_transactions:
        # Send the notification to Discord.
        response = send_discord_notification(transaction)
        notified_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response.status_code in (200, 204):  # Discord returns 204 on success sometimes
            log_notification(conn, transaction[0], transaction[1], notified_at, response.status_code)
            print(f"Notification sent for ptr_id {transaction[0]}, transaction {transaction[1]}.")
            total_new_notifications += 1
        else:
            error_msg = response.text
            log_notification(conn, transaction[0], transaction[1], notified_at, response.status_code, error_msg)
            print(f"Failed to send notification for ptr_id {transaction[0]}, transaction {transaction[1]}. Status: {response.status_code}")
        
        # Wait briefly between notifications.
        time.sleep(1)
    
    print(f"Total new notifications sent: {total_new_notifications}")
    conn.close()

if __name__ == "__main__":
    send_discord_notifications()
