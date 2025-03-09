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
    Send a notification to Discord using the webhook.
    The transaction tuple is expected to contain:
      (ptr_id, transaction_number, transaction_date, owner, ticker, asset_name,
       additional_info, asset_type, type, amount, comment, filing_date)
    """
    # Unpack transaction tuple for clarity:
    (ptr_id, txn_num, txn_date, owner, ticker, asset_name,
     additional_info, asset_type, txn_type, amount, comment, filing_date) = transaction

    # Construct a message string – feel free to adjust formatting as desired.
    message = (
        f"**New Transaction Notification**\n"
        f"**Filing Date:** {filing_date}\n"
        f"**Transaction Number:** {txn_num}\n"
        f"**Transaction Date:** {txn_date}\n"
        f"**Owner:** {owner}\n"
        f"**Ticker:** {ticker}\n"
        f"**Asset Name:** {asset_name}\n"
        f"**Additional Info:** {additional_info}\n"
        f"**Asset Type:** {asset_type}\n"
        f"**Type:** {txn_type}\n"
        f"**Amount:** {amount}\n"
        f"**Comment:** {comment}"
    )

    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    return response

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

if __name__ == "__main__":
    main()
