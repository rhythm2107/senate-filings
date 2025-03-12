import sqlite3
import datetime
import logging
from modules.config import DB_NAME

# Get the main_logger object
logger = logging.getLogger("main_logger")

# Basic DB Functions

def init_db(db_name=DB_NAME):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS filings (
            ptr_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            filing_info TEXT,
            filing_url TEXT,
            filing_date TEXT,
            filing_type TEXT,
            senator_id INTEGER
        )
    ''')
    conn.commit()
    return conn

def init_senators_tables(conn):
    """
    Create tables:
      - senators (one row per senator, with a canonical name)
      - senator_aliases (many possible aliases linked to senator_id)
    """
    c = conn.cursor()

    # Create the 'senators' table
    c.execute('''
        CREATE TABLE IF NOT EXISTS senators (
            senator_id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_full_name TEXT NOT NULL,
            state TEXT,
            party TEXT
            -- add any extra columns as needed
        )
    ''')

    # Create the 'senator_aliases' table
    c.execute('''
        CREATE TABLE IF NOT EXISTS senator_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            senator_id INTEGER NOT NULL,
            alias_name TEXT NOT NULL,
            UNIQUE(alias_name),
            FOREIGN KEY (senator_id) REFERENCES senators(senator_id)
        )
    ''')

    conn.commit()
    logger.debug("Senators tables (senators, senator_aliases) created/initialized if they did not exist.")

def get_senator_id_by_alias(conn, alias_name):
    """
    Given an alias_name (e.g., 'LADDA TAMMY DUCKWORTH'),
    returns the senator_id if we have it on file, else None.
    """
    c = conn.cursor()
    c.execute("SELECT senator_id FROM senator_aliases WHERE alias_name = ?", (alias_name,))
    row = c.fetchone()
    return row[0] if row else None

# NEW
def insert_alias_for_senator(conn, senator_id, alias_name):
    """
    Inserts a new alias into senator_aliases for the given senator_id.
    If alias_name already exists, it will skip due to UNIQUE(alias_name).
    """
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO senator_aliases (senator_id, alias_name)
            VALUES (?, ?)
        ''', (senator_id, alias_name))
        conn.commit()
        logger.debug(f"Inserted alias '{alias_name}' for senator_id={senator_id}.")
    except Exception as e:
        logger.exception(f"Failed to insert alias {alias_name}: {e}")
        conn.rollback()

# NEW
def insert_new_senator(conn, canonical_full_name, state="", party=""):
    """
    Inserts a new row into the senators table and returns the new senator_id.
    """
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO senators (canonical_full_name, state, party)
            VALUES (?, ?, ?)
        ''', (canonical_full_name, state, party))
        conn.commit()

        new_id = c.lastrowid  # senator_id autoincrement
        logger.debug(f"Inserted new senator '{canonical_full_name}' with senator_id={new_id}.")
        return new_id
    except Exception as e:
        logger.exception(f"Failed to insert new senator '{canonical_full_name}': {e}")
        conn.rollback()
        return None


def init_transactions_table(conn):
    logger.debug(f"Init_transaction_table has been called.")
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                ptr_id TEXT,
                transaction_number INTEGER,
                transaction_date TEXT,
                owner TEXT,
                ticker TEXT,
                asset_name TEXT,
                additional_info TEXT,
                asset_type TEXT,
                type TEXT,
                amount TEXT,
                comment TEXT,
                PRIMARY KEY (ptr_id, transaction_number)
            )
        ''')
        conn.commit()
        logger.debug(f"Init_transaction_table succeeded.")
    except Exception as e:
        logger.exception(f"Init_transaction_table failed: {e}")

def insert_transaction(conn, transaction):
    logger.debug(f"insert_transaction called with {transaction}")
    try:
        c = conn.cursor()
        c.execute(
            '''
            INSERT OR IGNORE INTO transactions (
                ptr_id, transaction_number, transaction_date, owner, ticker,
                asset_name, additional_info, asset_type, type, amount, comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            transaction
        )
        conn.commit()
        logger.debug(f"insert_transaction succeeded for ptr_id={transaction[0]}")
    except Exception as e:
        logger.exception(f"insert_transaction failed: {e}")
        raise

# Scraping Module DB Functions

def get_filing_ptr_ids(conn):
    """
    Retrieve ptr_ids from filings table that have not been processed and are marked as Online.
    """
    c = conn.cursor()
    c.execute("SELECT ptr_id FROM filings WHERE filing_type = 'Online'")
    all_ptr_ids = {row[0] for row in c.fetchall()}
    c.execute("SELECT DISTINCT ptr_id FROM transactions")
    processed_ptr_ids = {row[0] for row in c.fetchall()}
    return list(all_ptr_ids - processed_ptr_ids)

# Create or update the filing scrape log table.
def init_filing_scrape_log(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS filing_scrape_log (
            ptr_id TEXT PRIMARY KEY,
            scraped_at TEXT
        )
    ''')
    conn.commit()

# Insert a filing record into the filings table.
def insert_filing(conn, filing):
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO filings (ptr_id, first_name, last_name, full_name, filing_info, filing_url, filing_date, filing_type, senator_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', filing)
    conn.commit()

# Log the scraping event for a given filing (using ptr_id).
def insert_filing_scrape_log(conn, ptr_id):
    c = conn.cursor()
    scraped_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT OR IGNORE INTO filing_scrape_log (ptr_id, scraped_at)
        VALUES (?, ?)
    ''', (ptr_id, scraped_at))
    conn.commit()

# Notification System DB Functions

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
        SELECT t.ptr_id,
               t.transaction_number,
               t.transaction_date,
               t.owner,
               t.ticker, 
               t.asset_name,
               t.additional_info,
               t.asset_type,
               t.type,
               t.amount,
               t.comment,
               f.filing_date,
               s.canonical_full_name AS name
        FROM transactions t
        JOIN filings f ON t.ptr_id = f.ptr_id
        JOIN senators s ON f.senator_id = s.senator_id
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