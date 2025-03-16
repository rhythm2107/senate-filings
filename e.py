import sqlite3
import logging
from datetime import datetime

def setup_match_logger(log_file="matched_transactions.log"):
    """
    Sets up and returns a logger that writes matched transaction info to a file.
    """
    match_logger = logging.getLogger("match_logger")
    match_logger.setLevel(logging.DEBUG)
    if not match_logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        match_logger.addHandler(fh)
    return match_logger

def init_transactions_analytics_table(conn):
    """
    Creates the transactions_analytics table if it does not exist.
    
    The table includes:
      - ptr_id and transaction_number as a composite primary key.
      - senator_id: senator performing the transaction.
      - transaction_date, ticker, amount, owner: purchase details.
      - status: 'Closed' if a matching sale is found, 'Open' otherwise.
      - sale_ptr_id, sale_transaction_number, sale_date: details for the matching sale (if available).
    """
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions_analytics (
            ptr_id TEXT,
            transaction_number INTEGER,
            senator_id INTEGER,
            transaction_date TEXT,
            ticker TEXT,
            amount TEXT,
            owner TEXT,
            status TEXT,
            sale_ptr_id TEXT,
            sale_transaction_number INTEGER,
            sale_date TEXT,
            PRIMARY KEY (ptr_id, transaction_number)
        )
    """)
    conn.commit()


def match_transactions(conn):
    """
    Matches purchase transactions with sale transactions and returns a list of dictionaries.
    
    Each dictionary has keys:
      - purchase: {senator_id, ptr_id, txn_num, transaction_date, ticker, amount, owner}
      - sale: {ptr_id, txn_num, transaction_date, owner} if a matching sale was found, else None
    The matching criteria are:
      - Transaction type is "purchase" (asset type "Stock")
      - Sale must be for the same ticker and senator, with matching owner (case-insensitive)
      - Sale date (converted from MM/DD/YYYY using SQLite’s date() function) is greater than the purchase date.
      - Transactions are sorted chronologically.
      - Each sale (by composite key: ptr_id+txn_num) is used only once.
    Debug logs separate each purchase with a "----------" line and log all candidate sale transactions.
    """
    match_logger = setup_match_logger()
    c = conn.cursor()
    
    matched_sale_keys = set()  # composite keys (ptr_id, txn_number) for already matched sales
    results = []  # list of dictionaries holding match info
    
    # Retrieve purchase transactions (include owner), sorted chronologically.
    query_purchase = """
       SELECT f.senator_id, t.ptr_id, t.transaction_number, t.transaction_date, 
              t.ticker, t.amount, t.owner
       FROM transactions t
       JOIN filings f ON t.ptr_id = f.ptr_id
       WHERE LOWER(t.type) LIKE '%purchase%'
         AND LOWER(t.asset_type) = 'stock'
         AND t.ticker <> '--'
       ORDER BY date(substr(t.transaction_date,7,4) || '-' ||
                     substr(t.transaction_date,1,2) || '-' ||
                     substr(t.transaction_date,4,2)) ASC
    """
    c.execute(query_purchase)
    purchases = c.fetchall()
    
    match_logger.info(f"Total purchase transactions: {len(purchases)}")
    
    for purchase in purchases:
        senator_id, p_ptr, p_txn_num, p_date, ticker, p_amount, p_owner = purchase
        try:
            p_date_obj = datetime.strptime(p_date, "%m/%d/%Y").date()
        except Exception as e:
            match_logger.error(f"Error converting purchase date '{p_date}' for ptr_id {p_ptr}: {e}")
            continue
        
        match_logger.debug("---------- Start Purchase ----------")
        match_logger.debug(
            f"Purchase: senator_id={senator_id}, ptr_id={p_ptr}, txn_num={p_txn_num}, "
            f"raw date={p_date}, converted={p_date_obj}, ticker={ticker}, amount={p_amount}, owner={p_owner}"
        )
        
        # Retrieve all sale transactions for this senator and ticker, sorted by date.
        query_sale = """
           SELECT s.ptr_id, s.transaction_number, s.transaction_date, s.owner
           FROM transactions s
           JOIN filings fs ON s.ptr_id = fs.ptr_id
           WHERE s.ticker = ?
             AND fs.senator_id = ?
             AND LOWER(s.type) LIKE '%sale%'
             AND LOWER(s.asset_type) = 'stock'
             AND s.ticker <> '--'
           ORDER BY date(substr(s.transaction_date,7,4) || '-' ||
                          substr(s.transaction_date,1,2) || '-' ||
                          substr(s.transaction_date,4,2)) ASC
        """
        c.execute(query_sale, (ticker, senator_id))
        sales = c.fetchall()
        match_logger.debug(f"Found {len(sales)} sale transactions for purchase {p_ptr} (ticker {ticker}).")
        
        candidate_sales = []
        for sale in sales:
            s_ptr, s_txn_num, s_date, s_owner = sale
            try:
                s_date_obj = datetime.strptime(s_date, "%m/%d/%Y").date()
            except Exception as e:
                match_logger.error(f"Error converting sale date '{s_date}' for ptr_id {s_ptr}: {e}")
                continue
            
            match_logger.debug(
                f"Sale Candidate: ptr_id={s_ptr}, txn_num={s_txn_num}, raw date={s_date}, "
                f"converted={s_date_obj}, owner={s_owner}"
            )
            if s_date_obj > p_date_obj and s_owner.strip().lower() == p_owner.strip().lower():
                composite_key = (s_ptr, s_txn_num)
                if composite_key in matched_sale_keys:
                    match_logger.debug(f"Sale {composite_key} already matched; skipping.")
                    continue
                candidate_sales.append({
                    "ptr_id": s_ptr,
                    "txn_num": s_txn_num,
                    "transaction_date": s_date,
                    "date_obj": s_date_obj,
                    "owner": s_owner
                })
        
        if candidate_sales:
            for cand in candidate_sales:
                match_logger.debug(
                    f"Candidate Match: ptr_id={cand['ptr_id']}, txn_num={cand['txn_num']}, "
                    f"raw date={cand['transaction_date']}, converted={cand['date_obj']}, owner={cand['owner']}"
                )
            # Select the first candidate (chronologically).
            first_sale = candidate_sales[0]
            matched_sale_keys.add((first_sale["ptr_id"], first_sale["txn_num"]))
            match_logger.debug(
                f"Matching Sale for purchase {p_ptr}: ptr_id={first_sale['ptr_id']}, txn_num={first_sale['txn_num']}, "
                f"raw date={first_sale['transaction_date']}, converted={first_sale['date_obj']}, owner={first_sale['owner']}"
            )
        else:
            first_sale = None
            match_logger.debug(f"No matching sale found for purchase {p_ptr} with owner '{p_owner}'.")
        
        match_logger.debug("----------- End Purchase -----------\n")
        
        # Append the matching result.
        results.append({
            "purchase": {
                "senator_id": senator_id,
                "ptr_id": p_ptr,
                "txn_num": p_txn_num,
                "transaction_date": p_date,
                "ticker": ticker,
                "amount": p_amount,
                "owner": p_owner,
                "date_obj": p_date_obj
            },
            "sale": first_sale  # will be None if no match found
        })
    
    match_logger.info(f"Processed {len(purchases)} purchase transactions.")
    print("Length of results:", len(results))
    return results

def populate_transactions_analytics_from_matches(conn, matches):
    """
    Uses the matching results (from match_transactions) to populate the transactions_analytics table.
    
    Each match (dictionary) has:
      - purchase: dictionary of purchase details.
      - sale: dictionary of sale details (or None if not matched).
    
    The table will be populated with fields:
      - For purchase: senator_id, ptr_id, txn_num, transaction_date, ticker, amount, owner.
      - status: "Closed" if sale exists, else "Open".
      - For closed transactions, also sale_ptr_id, sale_txn_num, sale_date.
    """
    c = conn.cursor()
    
    for match in matches:
        purchase = match["purchase"]
        sale = match["sale"]
        status = "Closed" if sale is not None else "Open"
        sale_ptr_id = sale["ptr_id"] if sale else None
        sale_txn_num = sale["txn_num"] if sale else None
        sale_date = sale["transaction_date"] if sale else None
        
        c.execute("""
            INSERT OR REPLACE INTO transactions_analytics (
                ptr_id, senator_id, transaction_number, transaction_date,
                ticker, amount, owner, status, sale_ptr_id, sale_transaction_number, sale_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            purchase["ptr_id"],
            purchase["senator_id"],
            purchase["txn_num"],
            purchase["transaction_date"],
            purchase["ticker"],
            purchase["amount"],
            purchase["owner"],
            status,
            sale_ptr_id,
            sale_txn_num,
            sale_date
        ))
    conn.commit()
    print("transactions_analytics table populated successfully.")

# Example usage:
if __name__ == "__main__":
    conn = sqlite3.connect("filings.db")
    # Init transactions_analytics table
    init_transactions_analytics_table(conn)
    # First, perform matching:
    matches = match_transactions(conn)
    print(f"Found matches for {len(matches)} purchase transactions.")
    # Then, use those matches to populate the transactions_analytics table.
    populate_transactions_analytics_from_matches(conn, matches)
    print("Debug matching complete. Check 'matched_transactions.log' for details and verify transactions_analytics table.")
