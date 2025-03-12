import requests
import sqlite3
import datetime
import time
import logging
from modules.config import (
    DB_NAME,
    DISCORD_WEBHOOK_NOTIFICATION,
    DISCORD_WEBHOOK_DEBUG
)
from modules.db_helper import (
    init_notification_log,
    get_unnotified_transactions,
    log_notification
)

# Get the main_logger object
logger = logging.getLogger("main_logger")

# --- Notification Function ---

def send_single_discord_notification(transaction):
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
    response = requests.post(DISCORD_WEBHOOK_NOTIFICATION, json=payload)
    return response

def send_debug_notification_unknown_senator(ptr_id, alias_name):
    """
    Sends a simple notification to the Discord 'debug' channel if we discover
    an unrecognized senator name (i.e., no senator_id).
    """
    # Build a minimal embed or plain message
    embed = {
        "title": "Unknown Senator Name Detected",
        "description": (
            f"PTR ID: **{ptr_id}**\n"
            f"Unknown name: **{alias_name}**\n\n"
            "Manual review needed to assign the correct senator."
        ),
        "color": 15158332,  # a red-ish color to highlight error (optional)
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    payload = {
        "embeds": [embed],
        "allowed_mentions": { "parse": [] }  # don't ping anyone
    }

    response = requests.post(DISCORD_WEBHOOK_DEBUG, json=payload)
    logger.info(
        f"Debug notification sent for unknown senator alias '{alias_name}' (ptr_id={ptr_id}). "
        f"Status: {response.status_code}"
    )
    return response

# --- Main Process ---

def send_unnotified_discord_notifications():
    # Open the database connection
    conn = sqlite3.connect(DB_NAME)
    init_notification_log(conn)
    
    # Retrieve transactions that haven't been notified yet.
    unnotified_transactions = get_unnotified_transactions(conn)
    logger.info(f"Found {len(unnotified_transactions)} unnotified transactions.")
    
    total_new_notifications = 0
    for transaction in unnotified_transactions:
        # Send the notification to Discord.
        response = send_single_discord_notification(transaction)
        notified_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response.status_code in (200, 204):  # Discord returns 204 on success sometimes
            log_notification(conn, transaction[0], transaction[1], notified_at, response.status_code)
            logger.info(f"Notification sent for ptr_id {transaction[0]}, transaction {transaction[1]}.")
            total_new_notifications += 1
        else:
            error_msg = response.text
            log_notification(conn, transaction[0], transaction[1], notified_at, response.status_code, error_msg)
            logger.info(f"Failed to send notification for ptr_id {transaction[0]}, transaction {transaction[1]}. Status: {response.status_code}")
        
        # Wait briefly between notifications.
        time.sleep(3)
    
    logger.info(f"Total new notifications sent: {total_new_notifications}")
    conn.close()