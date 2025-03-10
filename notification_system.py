import requests
import sqlite3
import datetime
import time

# --- Configuration ---
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1348414232160505949/PRpkAqUYve11F7v8GROeVn95f9umtH-4trMPhLtAob8or-6RtukO2TeS8Vrf3WaWbKzM'  # Replace with your webhook URL
DB_NAME = 'filings.db'

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
         asset_name, additional_info, asset_type, type, amount, comment, filing_date)
    """
    c = conn.cursor()
    query = '''
        SELECT t.ptr_id, t.transaction_number, t.transaction_date, t.owner, t.ticker, 
               t.asset_name, t.additional_info, t.asset_type, t.type, t.amount, t.comment,
               f.filing_date
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
     additional_info, asset_type, txn_type, amount, comment, filing_date) = transaction

    # Build an embed payload
    embed = {
        "title": "New Transaction Notification",
        "color": 3447003,  # A blue color; you can change this value as desired.
        "fields": [
            {"name": "Filing Date", "value": filing_date, "inline": True},
            {"name": "Transaction Number", "value": str(txn_num), "inline": True},
            {"name": "Transaction Date", "value": txn_date, "inline": True},
            {"name": "Owner", "value": owner, "inline": True},
            {"name": "Ticker", "value": ticker, "inline": True},
            {"name": "Asset Name", "value": asset_name, "inline": False},
            {"name": "Additional Info", "value": additional_info if additional_info else "N/A", "inline": False},
            {"name": "Asset Type", "value": asset_type, "inline": True},
            {"name": "Type", "value": txn_type, "inline": True},
            {"name": "Amount", "value": amount, "inline": True},
            {"name": "Comment", "value": comment, "inline": False}
        ],
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "footer": {"text": "Your Application Name"}
    }

    payload = {"embeds": [embed]}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    return response





import requests


# Replace with your actual Discord webhook URL.

def test_discord_embed(transaction):
    """
    Sends a test Discord embed notification using dynamic transaction data.
    The embed format is inspired by the provided example, with:
      - Apple Inc. as the author (with image)
      - A colorful layout with a two-part embed:
          * The first embed contains detailed transaction information in fields.
          * The second embed displays transaction date and filing date separately.
    """
    # Unpack transaction tuple:
    (ptr_id, txn_num, txn_date, owner, ticker, asset_name, additional_info,
     asset_type, txn_type, amount, comment, filing_date) = transaction

    # Embed 1: Detailed Notification with rich formatting
    embed1 = {
        # "title": "title ~~(did you know you can have markdown here too?)~~",
        "description": "This is a new transaction from Senator Lamar Alexander. It seems that if i spread the text it sizes to the content amount so maybe its more readable this way.",
        "url": "https://discordapp.com",
        "color": 1538847,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "footer": {
            "icon_url": "https://i.imgur.com/J01MSXf.jpeg",
            "text": "footer text"
        },
        "thumbnail": {
            "url": "https://i.imgur.com/J01MSXf.jpeg"
        },
        "image": {
            # "url": "https://cdn.discordapp.com/embed/avatars/0.png"
        },
        "author": {
            "name": "Senator Lamar Alexander",
            "url": "https://discordapp.com",
            # "icon_url": "https://assets-netstorage.groww.in/intl-stocks/logos/AAPL.png"
        },
        "fields": [
            # {"name": "Transaction #", "value": str(txn_num), "inline": True},
            {"name": "Ticker", "value": ticker, "inline": False},
            {"name": "Owner", "value": owner, "inline": False},
            {"name": "Asset Name", "value": asset_name, "inline": True},
            {"name": "Asset Type", "value": asset_type, "inline": True},
            {"name": "Transaction Type", "value": txn_type, "inline": True},
            {"name": "Amount", "value": amount, "inline": True},
            # {"name": "Additional Info", "value": additional_info if additional_info else "N/A", "inline": False},
            # {"name": "Comment", "value": comment, "inline": False},
            {"name": "Filing Date", "value": filing_date, "inline": True},
            {"name": "Transaction Date", "value": txn_date, "inline": True},
        ]
    }

    # Embed 2: Information Section with Transaction Date and Filing Date
    embed2 = {
        "color": 7538847,
        "description": f"\n**Transaction Date**: {txn_date}\n**Filing Date**: {filing_date}"
    }

    payload = {
        "content": None,
        "embeds": [embed1],
        "attachments": []
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code in (200, 204):
        print("Test embed sent successfully! Status code:", response.status_code)
    else:
        print("Failed to send test embed. Status code:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    # Example transaction tuple:
    sample_transaction = (
        "a0a26d20-b140-444b-b562-9d73de4c6bd9",  # ptr_id
        1,                                      # Transaction Number
        "03/11/2015",                           # Transaction Date
        "Spouse",                               # Owner
        "AAPL",                                   # Ticker
        "International Paper Company (NYSE)",          # Asset Name
        "",   # Additional Info
        "Municipal Security",                       # Asset Type
        "Sale (Partial)",                          # Type
        "$500,001 - $1,000,000",                      # Amount
        "--",                                   # Comment
        "10/02/2015"                            # Filing Date
    )
    test_discord_embed(sample_transaction)





# --- Main Process ---

def main():
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

# if __name__ == "__main__":
#     main()
