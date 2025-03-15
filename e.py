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

def debug_match_transactions_python(conn):
    """
    For each purchase transaction (asset type 'Stock'),
    retrieves all sale transactions for the same senator and ticker,
    converts the date strings to Python date objects,
    and then compares them in Python.
    
    It logs:
      - the raw and converted purchase date,
      - each sale's raw and converted date,
      - and if a matching sale is found, only the first match is logged.
      
    Finally, it logs and prints the total number of purchases processed,
    how many had at least one matching sale, and how many did not.
    """
    match_logger = setup_match_logger()
    c = conn.cursor()
    
    # Retrieve purchase transactions.
    query_purchase = """
       SELECT f.senator_id, t.ptr_id, t.transaction_number, t.transaction_date, t.ticker, t.amount
       FROM transactions t
       JOIN filings f ON t.ptr_id = f.ptr_id
       WHERE LOWER(t.type) LIKE '%purchase%'
         AND LOWER(t.asset_type) = 'stock'
         AND t.ticker <> '--'
       ORDER BY t.transaction_date ASC
    """
    c.execute(query_purchase)
    purchases = c.fetchall()
    
    total_purchases = len(purchases)
    matched_count = 0
    unmatched_count = 0
    
    for purchase in purchases:
        senator_id, p_ptr, p_txn_num, p_date, ticker, p_amount = purchase
        
        # Convert purchase date from MM/DD/YYYY to a Python date object.
        try:
            p_date_obj = datetime.strptime(p_date, "%m/%d/%Y").date()
        except Exception as e:
            match_logger.error(f"Error converting purchase date '{p_date}' for transaction {p_ptr}: {e}")
            continue
        
        match_logger.debug(
            f"Purchase: senator_id={senator_id}, ptr_id={p_ptr}, txn_num={p_txn_num}, "
            f"raw date={p_date}, converted={p_date_obj}, ticker={ticker}, amount={p_amount}"
        )
        
        # Retrieve all sale transactions for this senator and ticker (without date filtering).
        query_sale = """
           SELECT s.ptr_id, s.transaction_number, s.transaction_date, s.ticker, s.amount
           FROM transactions s
           JOIN filings fs ON s.ptr_id = fs.ptr_id
           WHERE s.ticker = ?
             AND fs.senator_id = ?
             AND LOWER(s.type) LIKE '%sale%'
             AND LOWER(s.asset_type) = 'stock'
             AND s.ticker <> '--'
           ORDER BY s.transaction_date ASC
        """
        c.execute(query_sale, (ticker, senator_id))
        sales = c.fetchall()
        match_logger.debug(f"Found {len(sales)} sale transactions for purchase {p_ptr} (ticker {ticker}).")
        
        first_matching_sale = None
        for sale in sales:
            s_ptr, s_txn_num, s_date, s_ticker, s_amount = sale
            try:
                s_date_obj = datetime.strptime(s_date, "%m/%d/%Y").date()
            except Exception as e:
                match_logger.error(f"Error converting sale date '{s_date}' for transaction {s_ptr}: {e}")
                continue
            
            match_logger.debug(
                f"Sale: ptr_id={s_ptr}, txn_num={s_txn_num}, raw date={s_date}, converted={s_date_obj}, "
                f"ticker={s_ticker}, amount={s_amount}"
            )
            # Compare in Python: we want the first sale with a date greater than the purchase date.
            if s_date_obj > p_date_obj:
                first_matching_sale = (s_ptr, s_txn_num, s_date, s_date_obj, s_ticker, s_amount)
                break  # Found the first matching sale, stop checking further.
        
        if first_matching_sale:
            matched_count += 1
            s_ptr, s_txn_num, s_date, s_date_obj, s_ticker, s_amount = first_matching_sale
            match_logger.debug(
                f"Matching Sale for purchase {p_ptr}: ptr_id={s_ptr}, txn_num={s_txn_num}, "
                f"raw date={s_date}, converted={s_date_obj}, ticker={s_ticker}, amount={s_amount}"
            )
        else:
            unmatched_count += 1
            match_logger.debug(f"No matching sale (sale date > purchase date) found for purchase {p_ptr}.")
    
    match_logger.info(f"Processed {total_purchases} purchase transactions.")
    match_logger.info(f"Matched: {matched_count} purchase transactions have a matching sale (first match only).")
    match_logger.info(f"Unmatched: {unmatched_count} purchase transactions have no matching sale.")
    
    print(f"Total Purchases Processed: {total_purchases}")
    print(f"Total Matched Purchases: {matched_count}")
    print(f"Total Unmatched Purchases: {unmatched_count}")

if __name__ == "__main__":
    conn = sqlite3.connect("filings.db")
    debug_match_transactions_python(conn)
    print("Debug matching complete. Check 'matched_transactions.log' for details.")
