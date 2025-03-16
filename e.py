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
    and compares them in Python.
    
    It logs:
      - A separator line before and after each purchase.
      - The raw and converted purchase date and owner.
      - All candidate sale transactions (raw and converted) that satisfy:
            sale date > purchase date AND matching owner,
        unless the sale has already been matched (using a composite key of ptr_id & transaction_number).
      - Then logs the first matching sale (if any) used as the match.
      
    It also counts and prints the total number of purchases processed,
    how many had at least one matching sale, and how many did not.
    """
    match_logger = setup_match_logger()
    c = conn.cursor()
    
    # Maintain a set of sale composite keys (ptr_id, txn_number) that have been matched.
    matched_sale_keys = set()
    
    # Retrieve purchase transactions, sorted chronologically.
    query_purchase = """
       SELECT f.senator_id, t.ptr_id, t.transaction_number, t.transaction_date, 
              t.ticker, t.amount, t.owner
       FROM transactions t
       JOIN filings f ON t.ptr_id = f.ptr_id
       WHERE LOWER(t.type) LIKE '%purchase%'
         AND LOWER(t.asset_type) = 'stock'
         AND t.ticker <> '--'
       ORDER BY date(substr(t.transaction_date,7,4) || '-' || substr(t.transaction_date,1,2) || '-' || substr(t.transaction_date,4,2)) ASC;
    """
    c.execute(query_purchase)
    purchases = c.fetchall()
    
    total_purchases = len(purchases)
    matched_count = 0
    unmatched_count = 0
    
    for purchase in purchases:
        senator_id, p_ptr, p_txn_num, p_date, ticker, p_amount, p_owner = purchase
        
        match_logger.debug("---------- Start Purchase ----------")
        
        # Convert purchase date (assumed MM/DD/YYYY) to a Python date.
        try:
            p_date_obj = datetime.strptime(p_date, "%m/%d/%Y").date()
        except Exception as e:
            match_logger.error(f"Error converting purchase date '{p_date}' for transaction {p_ptr}: {e}")
            continue
        
        match_logger.debug(
            f"Purchase: senator_id={senator_id}, ptr_id={p_ptr}, txn_num={p_txn_num}, "
            f"raw date={p_date}, converted={p_date_obj}, ticker={ticker}, amount={p_amount}, owner={p_owner}"
        )
        
        # Retrieve all sale transactions for this senator and ticker, sorted chronologically.
        query_sale = """
           SELECT s.ptr_id, s.transaction_number, s.transaction_date, s.ticker, s.amount, s.owner
           FROM transactions s
           JOIN filings fs ON s.ptr_id = fs.ptr_id
           WHERE s.ticker = ?
             AND fs.senator_id = ?
             AND LOWER(s.type) LIKE '%sale%'
             AND LOWER(s.asset_type) = 'stock'
             AND s.ticker <> '--'
           ORDER BY date(substr(s.transaction_date,7,4) || '-' || substr(s.transaction_date,1,2) || '-' || substr(s.transaction_date,4,2)) ASC
        """
        c.execute(query_sale, (ticker, senator_id))
        sales = c.fetchall()
        match_logger.debug(f"Found {len(sales)} sale transactions for purchase {p_ptr} (ticker {ticker}).")
        
        candidate_sales = []
        first_matching_sale = None
        
        for sale in sales:
            s_ptr, s_txn_num, s_date, s_ticker, s_amount, s_owner = sale
            try:
                s_date_obj = datetime.strptime(s_date, "%m/%d/%Y").date()
            except Exception as e:
                match_logger.error(f"Error converting sale date '{s_date}' for transaction {s_ptr}: {e}")
                continue
            
            match_logger.debug(
                f"Sale Candidate: ptr_id={s_ptr}, txn_num={s_txn_num}, raw date={s_date}, "
                f"converted={s_date_obj}, ticker={s_ticker}, amount={s_amount}, owner={s_owner}"
            )
            # Compare in Python: sale must be after purchase and owner must match.
            if s_date_obj > p_date_obj and s_owner.strip().lower() == p_owner.strip().lower():
                composite_key = (s_ptr, s_txn_num)
                if composite_key in matched_sale_keys:
                    match_logger.debug(f"Sale {composite_key} already matched; skipping.")
                    continue
                candidate_sales.append((s_ptr, s_txn_num, s_date, s_date_obj, s_ticker, s_amount, s_owner))
        
        # Log all candidate matches.
        if candidate_sales:
            for cand in candidate_sales:
                s_ptr, s_txn_num, s_date, s_date_obj, s_ticker, s_amount, s_owner = cand
                match_logger.debug(
                    f"Candidate Match: ptr_id={s_ptr}, txn_num={s_txn_num}, raw date={s_date}, "
                    f"converted={s_date_obj}, ticker={s_ticker}, amount={s_amount}, owner={s_owner}"
                )
            # Select the first candidate (chronologically).
            first_matching_sale = candidate_sales[0]
        
        if first_matching_sale:
            matched_count += 1
            s_ptr, s_txn_num, s_date, s_date_obj, s_ticker, s_amount, s_owner = first_matching_sale
            match_logger.debug(
                f"Matching Sale for purchase {p_ptr}: ptr_id={s_ptr}, txn_num={s_txn_num}, "
                f"raw date={s_date}, converted={s_date_obj}, ticker={s_ticker}, amount={s_amount}, owner={s_owner}"
            )
            # Mark this sale as matched by its composite key.
            matched_sale_keys.add((s_ptr, s_txn_num))
        else:
            unmatched_count += 1
            match_logger.debug(f"No matching sale found for purchase {p_ptr} with owner '{p_owner}'.")
        
        match_logger.debug("----------- End Purchase -----------\n")
    
    match_logger.info(f"Processed {total_purchases} purchase transactions.")
    match_logger.info(f"Matched: {matched_count} purchases have a matching sale (first match chosen).")
    match_logger.info(f"Unmatched: {unmatched_count} purchases have no matching sale.")
    
    print(f"Total Purchases Processed: {total_purchases}")
    print(f"Total Matched Purchases: {matched_count}")
    print(f"Total Unmatched Purchases: {unmatched_count}")

if __name__ == "__main__":
    conn = sqlite3.connect("filings.db")
    debug_match_transactions_python(conn)
    print("Debug matching complete. Check 'matched_transactions.log' for details.")
