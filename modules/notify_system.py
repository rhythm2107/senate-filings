import requests
import sqlite3
import datetime
import time
import logging
from modules.config import (
    DB_NAME,
    DISCORD_WEBHOOK_NOTIFICATION_FREE,
    DISCORD_WEBHOOK_NOTIFICATION_STOCK,
    DISCORD_WEBHOOK_NOTIFICATION_LARGE,
    DISCORD_WEBHOOK_NOTIFICATION_OTHER,
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

def build_standard_embed(transaction):
    """
    Build the standard embed dictionary based on the transaction tuple.
    The transaction tuple is expected to have this structure:
    (ptr_id, txn_num, txn_date, owner, ticker, asset_name,
     additional_info, asset_type, txn_type, amount, comment, filing_date, name)
    """
    (ptr_id, txn_num, txn_date, owner, ticker, asset_name,
     additional_info, asset_type, txn_type, amount, comment, filing_date, name) = transaction
    embed = {
        "title": f"Senator {name}",
        "description": f"A new transaction from Senator {name}!",
        "color": 3447003,
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
    return embed

def send_transaction_notifications(transaction):
    responses = []
    
    # Unpack transaction (same as before)
    ptr_id, txn_num, txn_date, owner, ticker, asset_name, additional_info, asset_type, txn_type, amount, comment, filing_date, name = transaction
    
    # Build the standard embed
    standard_embed = build_standard_embed(transaction)
    
    # 1. Large Channel (if applicable)
    large_amounts = [
        "Over $50,000,000",
        "$25,000,001-$50,000,000",
        "$5,000,001-$25,000,000",
        "$1,000,001-$5,000,000",
        "$500,001-$1,000,000"
    ]
    if amount.strip() in large_amounts:
        large_embed = {
            "title": "💰 **LARGE TRANSACTION WAS DETECTED!** 💰",
            "description": "",
            "color": 15158332
        }
        embeds = [large_embed, standard_embed]
        responses.append(send_transaction_discord_notification(transaction, DISCORD_WEBHOOK_NOTIFICATION_LARGE, embeds=embeds))
        time.sleep(2)
    
    # 2. VIP Channels
    if asset_type.strip().lower() == "stock":
        responses.append(send_transaction_discord_notification(transaction, DISCORD_WEBHOOK_NOTIFICATION_STOCK))
    else:
        responses.append(send_transaction_discord_notification(transaction, DISCORD_WEBHOOK_NOTIFICATION_OTHER))
    time.sleep(2)
    
    # 3. Free Channel (all transactions)
    responses.append(send_transaction_discord_notification(transaction, DISCORD_WEBHOOK_NOTIFICATION_FREE))
    time.sleep(2)
    
    return responses


def send_transaction_discord_notification(transaction, webhook_url, embeds=None):
    """
    Sends a Discord notification via a webhook.
    If `embeds` is not provided, it sends a standard embed built from the transaction.
    """
    if embeds is None:
        # Use the standard embed
        embeds = [build_standard_embed(transaction)]
    payload = {
        "content": None,
        "embeds": embeds,
        "attachments": [],
        "allowed_mentions": {"roles": []}
    }
    response = requests.post(webhook_url, json=payload)
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
    
    unnotified_transactions = get_unnotified_transactions(conn)
    logger.info(f"Found {len(unnotified_transactions)} unnotified transactions.")
    
    total_new_notifications = 0
    for transaction in unnotified_transactions:
        responses = send_transaction_notifications(transaction)
        notified_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if all responses are successful
        if all(r.status_code in (200, 204) for r in responses):
            log_notification(conn, transaction[0], transaction[1], notified_at, 200)  # using 200 as a success code
            logger.info(f"Notification sent for ptr_id {transaction[0]}, transaction {transaction[1]}.")
            total_new_notifications += 1
        else:
            # If any response failed, log the error. You might combine responses or log the first failure.
            error_msg = "; ".join(r.text for r in responses if r.status_code not in (200, 204))
            log_notification(conn, transaction[0], transaction[1], notified_at, 400, error_msg)
            logger.info(f"Failed to send notification for ptr_id {transaction[0]}, transaction {transaction[1]}.")
        
        time.sleep(3)
    
    logger.info(f"Total new notifications sent: {total_new_notifications}")
    conn.close()
