import requests
import sqlite3
import re
import time
from bs4 import BeautifulSoup

# Base URL for PTR details
BASE_PTR_URL = "https://efdsearch.senate.gov/search/view/ptr/"

#############################################
# Database helper functions

def init_db(db_name="filings.db"):
    """Initialize the filings database with filings table if not exists."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS filings (
            ptr_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            filing_info TEXT,
            filing_url TEXT,
            filing_date TEXT
        )
    ''')
    conn.commit()
    return conn

def init_transactions_table(conn):
    """Initialize the transactions table to store transaction details.
    We use a composite primary key on (ptr_id, transaction_number) to avoid duplicate inserts.
    """
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

def get_filing_ptr_ids(conn):
    """Retrieve ptr_ids from filings table that have not been processed.
    Here, we assume a filing is 'processed' if it already has at least one transaction record.
    """
    c = conn.cursor()
    # Select all ptr_ids from filings
    c.execute("SELECT ptr_id FROM filings")
    all_ptr_ids = {row[0] for row in c.fetchall()}
    
    # Select ptr_ids that already have transactions scraped
    c.execute("SELECT DISTINCT ptr_id FROM transactions")
    processed_ptr_ids = {row[0] for row in c.fetchall()}
    
    # Return only new ones
    return list(all_ptr_ids - processed_ptr_ids)

def insert_transaction(conn, transaction):
    """Insert a single transaction record into the transactions table."""
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO transactions (
            ptr_id, transaction_number, transaction_date, owner, ticker, asset_name, additional_info, asset_type, type, amount, comment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', transaction)
    conn.commit()

#############################################
# Scraping functions

def scrape_transactions_for_ptr(ptr_id):
    """Given a ptr_id, scrape the corresponding page for transaction details.
    Returns a list of transaction tuples.
    """
    url = f"{BASE_PTR_URL}{ptr_id}/"
    print(f"Scraping transactions from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve {url}, status code {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    transactions = []

    # Find the table in the transactions div
    table = soup.find("div", class_="table-responsive")
    if table is None:
        print(f"No transaction table found for ptr_id {ptr_id}")
        return transactions

    table = table.find("table", class_="table")
    if table is None:
        print(f"No transaction table element found for ptr_id {ptr_id}")
        return transactions

    tbody = table.find("tbody")
    if tbody is None:
        print(f"No tbody found for ptr_id {ptr_id}")
        return transactions

    # Iterate over each row in the table body
    rows = tbody.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 9:
            # If there are fewer columns than expected, skip this row.
            continue

        # Extract text and strip whitespace
        transaction_number = cols[0].get_text(strip=True)
        transaction_date   = cols[1].get_text(strip=True)
        owner              = cols[2].get_text(strip=True)
        ticker             = cols[3].get_text(strip=True)
        asset_cell         = cols[4]
        # The asset cell may contain extra info in a nested <div>
        asset_name = asset_cell.get_text(separator=" ", strip=True)
        # Optionally, try to extract additional info (like Rate/Coupon and Matures) separately
        additional_div = asset_cell.find("div", class_="text-muted")
        additional_info = additional_div.get_text(separator=" ", strip=True) if additional_div else ""
        asset_type         = cols[5].get_text(strip=True)
        txn_type           = cols[6].get_text(strip=True)
        amount             = cols[7].get_text(strip=True)
        comment            = cols[8].get_text(strip=True)

        # Build a tuple; cast transaction_number to integer if possible.
        try:
            txn_num_int = int(transaction_number)
        except ValueError:
            txn_num_int = None

        transaction_tuple = (
            ptr_id,
            txn_num_int,
            transaction_date,
            owner,
            ticker,
            asset_name,
            additional_info,
            asset_type,
            txn_type,
            amount,
            comment
        )
        transactions.append(transaction_tuple)

    return transactions

#############################################
# Main processing

def main():
    conn = init_db()
    init_transactions_table(conn)
    
    # Get all ptr_ids from filings that haven't been processed yet.
    ptr_ids_to_scrape = get_filing_ptr_ids(conn)
    print(f"Found {len(ptr_ids_to_scrape)} new filings to process.")

    total_new_transactions = 0
    for ptr_id in ptr_ids_to_scrape:
        transactions = scrape_transactions_for_ptr(ptr_id)
        print(f"Found {len(transactions)} transactions for ptr_id {ptr_id}")
        for txn in transactions:
            insert_transaction(conn, txn)
            total_new_transactions += 1
        # Optional: add a short delay to be respectful of the server.
        time.sleep(2)
    
    print(f"Inserted a total of {total_new_transactions} new transaction records.")
    conn.close()

if __name__ == "__main__":
    main()
