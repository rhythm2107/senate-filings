import requests
import sqlite3
import re
import time
import logging
from bs4 import BeautifulSoup
from modules.config import PROXY
from modules.db_helper import init_db, init_transactions_table, get_filing_ptr_ids, insert_transaction
from modules.session_utilis import get_csrf_token, accept_disclaimer

# Get the main_logger object
logger = logging.getLogger("main_logger")

# --- Scraping Function ---

def scrape_transactions_for_ptr(session, headers, ptr_id):
    url = f"https://efdsearch.senate.gov/search/view/ptr/{ptr_id}/"
    print(f"Scraping transactions from: {url}")
    
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve {url}, status code {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    transactions = []
    
    table_div = soup.find("div", class_="table-responsive")
    if not table_div:
        print(f"No table-responsive div found for ptr_id {ptr_id}")
        return transactions
    
    table = table_div.find("table", class_="table")
    if not table:
        print(f"No table found in table-responsive div for ptr_id {ptr_id}")
        return transactions
    
    tbody = table.find("tbody")
    if not tbody:
        print(f"No tbody found for ptr_id {ptr_id}")
        return transactions
    
    rows = tbody.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 9:
            continue  # Skip rows that don't have enough columns.
        
        transaction_number = cols[0].get_text(strip=True)
        transaction_date   = cols[1].get_text(strip=True)
        owner              = cols[2].get_text(strip=True)
        ticker             = cols[3].get_text(strip=True)
        asset_cell         = cols[4]
        additional_div     = asset_cell.find("div", class_="text-muted")
        
        if additional_div:
            additional_info = additional_div.get_text(separator=" ", strip=True)
            additional_div.extract()  # Remove the additional info from asset_cell.
        else:
            additional_info = ""

        asset_name         = asset_cell.get_text(separator=" ", strip=True)
        additional_info    = additional_div.get_text(separator=" ", strip=True) if additional_div else ""
        asset_type         = cols[5].get_text(strip=True)
        txn_type           = cols[6].get_text(strip=True)
        amount             = cols[7].get_text(strip=True)
        comment            = cols[8].get_text(strip=True)
        
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

# --- Main Function ---

def scrape_transactions():
    # Optional: set proxy if needed
    proxy = {"http": PROXY}
    
    # Create a persistent session.
    session = requests.Session()
    
    # Prepare initial headers.
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9,pl;q=0.8',
        'Connection': 'keep-alive',
        'Content-Length': '1385',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'efdsearch.senate.gov',
        'Origin': 'https://efdsearch.senate.gov',
        'Referer': 'https://efdsearch.senate.gov/search/',
        'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'X-Csrftoken': 'placeholder'
    }
    headers = get_csrf_token(session, headers)
    
    # Accept the disclaimer to establish a valid session.
    csrftoken, session_id, number_token = accept_disclaimer(session, proxy=proxy)
    
    # Prepare headers for PTR scraping using our established tokens.
    ptr_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': headers['User-Agent'],
        'Cookie': f'csrftoken={csrftoken}; sessionid={session_id}; 33a5c6d97f299a223cb6fc3925909ef7={number_token}'
    }
    
    # Initialize the database and tables.
    conn = init_db()
    init_transactions_table(conn)
    
    # Get the list of ptr_ids to process (only Online filings).
    ptr_ids_to_scrape = get_filing_ptr_ids(conn)
    print(f"Found {len(ptr_ids_to_scrape)} new filings to process.")
    
    total_new_transactions = 0
    for ptr_id in ptr_ids_to_scrape:
        transactions = scrape_transactions_for_ptr(session, ptr_headers, ptr_id)
        print(f"Found {len(transactions)} transactions for ptr_id {ptr_id}")
        for txn in transactions:
            insert_transaction(conn, txn)
            total_new_transactions += 1
        time.sleep(2)  # Be respectful to the server.
    
    print(f"Inserted a total of {total_new_transactions} new transaction records.")
    conn.close()