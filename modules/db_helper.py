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