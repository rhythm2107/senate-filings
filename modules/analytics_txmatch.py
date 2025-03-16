import sqlite3
import logging
import time
import yfinance as yf
from datetime import datetime, timedelta
from modules.logger import setup_logger
from modules.utilis import get_ignore_tickers, average_amount
from modules.db_helper import init_transactions_analytics_table

logger = logging.getLogger("analytics")

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

def fetch_all_ticker_histories(conn, overall_start_date, overall_end_date, ignore_file="resources/ignore_tickers.txt"):
    """
    Fetch a dictionary mapping each unique ticker to its historical data
    between overall_start_date and overall_end_date.
    Tickers in the ignore file are skipped.
    """
    c = conn.cursor()   
    c.execute("""
        SELECT DISTINCT t.ticker
        FROM transactions_analytics t
        WHERE t.ticker <> '--'
    """)
    tickers = [row[0].lstrip('$') for row in c.fetchall()]
    print("Total Distinct Tickers Found:", len(tickers))
    ignore_tickers = get_ignore_tickers(ignore_file)
    logger.info(f"Ignore tickers: {ignore_tickers}")

    ticker_histories = {}
    failed_tickers = []
    for ticker in tickers:
        if ticker in ignore_tickers:
            logger.info(f"Ticker {ticker} is in the ignore list. Skipping.")
            continue
        logger.debug(f"Fetching history for {ticker} from {overall_start_date} to {overall_end_date}")
        stock = yf.Ticker(ticker)
        try:
            hist = stock.history(start=overall_start_date.strftime("%Y-%m-%d"),
                                   end=overall_end_date.strftime("%Y-%m-%d"),
                                   interval="1d",
                                   actions=False)
            time.sleep(1)
            if hist.empty:
                logger.warning(f"No data for {ticker} between {overall_start_date} and {overall_end_date}.")
                failed_tickers.append(ticker)
            else:
                ticker_histories[ticker] = hist
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            failed_tickers.append(ticker)
    if failed_tickers:
        logger.info(f"Tickers that failed to fetch: {failed_tickers}")
    return ticker_histories

def get_price_from_history(ticker, target_date, ticker_histories, max_offset=5):
    """
    Return the closing price for a given ticker from the pre-fetched history (ticker_histories)
    for the target_date. If the price is not available on target_date (e.g. due to a non-trading day),
    it will search backward day-by-day (up to max_offset days) for the most recent available price.
    
    Parameters:
      - ticker: the stock ticker (string)
      - target_date: a datetime.date object representing the date to check
      - ticker_histories: a dictionary mapping tickers to their historical DataFrame (from yfinance)
      - max_offset: maximum number of days to search backward
      
    Returns:
      The closing price (float) if found, or None if no price is available.
    """
    ticker = ticker.lstrip('$')
    if ticker not in ticker_histories:
        return None
    hist = ticker_histories[ticker]
    available_dates = [d.strftime("%Y-%m-%d") for d in hist.index]
    
    # Try target_date, then go backwards.
    for offset in range(0, max_offset + 1):
        new_date = target_date - timedelta(days=offset)
        new_date_str = new_date.strftime("%Y-%m-%d")
        if new_date_str in available_dates:
            return hist.loc[new_date_str]["Close"]
    return None

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
                purchase_ptr_id, senator_id, purchase_transaction_number, purchase_date,
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

def update_transactions_prices(conn, ticker_histories, max_offset=5):
    """
    Fetches all transactions from the transactions_analytics table (using its composite key),
    and for each transaction, checks for the closing price on the following dates:
      - purchase_date
      - purchase_date + 7 days
      - purchase_date + 30 days
      - today's date
      - sale_date (if available and if status is "Closed")
    
    If a price is not found on the given date, the function uses get_price_with_fallback
    to search forward (or backward if the new date would be in the future) up to max_offset days.
    
    Then, the row in transactions_analytics is updated with these price values.
    """
    c = conn.cursor()
    # Fetch necessary columns from transactions_analytics.
    c.execute("""
        SELECT purchase_ptr_id, purchase_transaction_number, purchase_date, ticker, status, sale_date
        FROM transactions_analytics
    """)
    rows = c.fetchall()
    today = datetime.utcnow().date()
    
    for row in rows:
        purchase_ptr_id, purchase_txn_num, purchase_date_str, ticker, status, sale_date_str = row
        try:
            purchase_date = datetime.strptime(purchase_date_str, "%m/%d/%Y").date()
        except Exception as e:
            print(f"Error converting purchase_date '{purchase_date_str}' for {purchase_ptr_id}: {e}")
            continue
        
        # Get price for purchase_date
        price_on_purchase = get_price_from_history(ticker, purchase_date, ticker_histories, max_offset)
        # Price 7 days after purchase
        date_7d = purchase_date + timedelta(days=7)
        price_7d = get_price_from_history(ticker, date_7d, ticker_histories, max_offset)
        # Price 30 days after purchase
        date_30d = purchase_date + timedelta(days=30)
        price_30d = get_price_from_history(ticker, date_30d, ticker_histories, max_offset)
        # Price for today
        price_today = get_price_from_history(ticker, today, ticker_histories, max_offset)
        # Price on sale date, if status is "Closed" and sale_date is present.
        price_on_sale = None
        if status.strip().lower() == "closed" and sale_date_str:
            try:
                sale_date = datetime.strptime(sale_date_str, "%m/%d/%Y").date()
                price_on_sale = get_price_from_history(ticker, sale_date, ticker_histories, max_offset)
            except Exception as e:
                print(f"Error converting sale_date '{sale_date_str}' for {purchase_ptr_id}: {e}")
        
        # Update the row with the new price data.
        c.execute("""
            UPDATE transactions_analytics
            SET price_on_purchase = ?,
                price_7d = ?,
                price_30d = ?,
                price_today = ?,
                price_on_sale = ?
            WHERE purchase_ptr_id = ? AND purchase_transaction_number = ?
        """, (
            price_on_purchase,
            price_7d,
            price_30d,
            price_today,
            price_on_sale,
            purchase_ptr_id,
            purchase_txn_num
        ))
    conn.commit()
    print("Updated transactions_analytics with price data.")

def update_transactions_analytics_calculations(conn):
    """
    For each row in transactions_analytics, calculates:
      - percent_7d (if price_on_purchase and price_7d exist)
      - percent_30d (if price_on_purchase and price_30d exist)
      - For status "Open": percent_today, net_profit (using percent_today), and current_value.
      - For status "Closed": percent_on_sale, net_profit (using percent_on_sale), and current_value.
    
    The average invested is computed via the average_amount() helper using the 'amount' field.
    If any required field is missing (i.e. price_on_purchase, price_today/price_on_sale), that row is skipped.
    """
    c = conn.cursor()
    c.execute("""
        SELECT purchase_ptr_id, purchase_transaction_number, status, amount,
               price_on_purchase, price_7d, price_30d, price_today, price_on_sale
        FROM transactions_analytics
    """)
    rows = c.fetchall()
    updated_count = 0

    for row in rows:
        (purchase_ptr_id, purchase_txn_num, status, amount_str,
         price_on_purchase, price_7d, price_30d, price_today, price_on_sale) = row
        
        # We require price_on_purchase.
        if price_on_purchase is None:
            continue

        # Calculate percent_7d and percent_30d if available.
        percent_7d = ((price_7d - price_on_purchase) / price_on_purchase * 100) if price_7d is not None else None
        percent_30d = ((price_30d - price_on_purchase) / price_on_purchase * 100) if price_30d is not None else None
        
        # Use average_amount() to get the average invested value.
        avg_invested = average_amount(amount_str)
        if avg_invested is None:
            continue

        # Depending on status, compute percent_today or percent_on_sale,
        # then net_profit and current_value.
        if status.strip().lower() == "open":
            if price_today is None:
                continue
            percent_today = ((price_today - price_on_purchase) / price_on_purchase * 100)
            percent_on_sale = None
            net_profit = avg_invested * (percent_today / 100)
            current_value = avg_invested + net_profit
        elif status.strip().lower() == "closed":
            if price_on_sale is None:
                continue
            percent_on_sale = ((price_on_sale - price_on_purchase) / price_on_purchase * 100)
            percent_today = None
            net_profit = avg_invested * (percent_on_sale / 100)
            current_value = avg_invested + net_profit
        else:
            continue

        c.execute("""
            UPDATE transactions_analytics
            SET percent_7d = ?,
                percent_30d = ?,
                percent_today = ?,
                percent_on_sale = ?,
                net_profit = ?,
                current_value = ?
            WHERE purchase_ptr_id = ? AND purchase_transaction_number = ?
        """, (
            percent_7d,
            percent_30d,
            percent_today,
            percent_on_sale,
            net_profit,
            current_value,
            purchase_ptr_id,
            purchase_txn_num
        ))
        updated_count += 1

    conn.commit()
    print(f"Updated calculations for {updated_count} transactions in transactions_analytics.")


def process_transactions_analytics(conn):
    """
    Runs the full pipeline to build and update the transactions_analytics table:
      - Initializes the table.
      - Matches purchase transactions to sale transactions.
      - Populates the transactions_analytics table with matching data.
      - Fetches historical price data for distinct tickers.
      - Updates each transaction row with price data.
      - Calculates additional metrics (percentages, net profit, current value).
    """
    init_transactions_analytics_table(conn)
    
    # Match transactions.
    matches = match_transactions(conn)
    print(f"Found matches for {len(matches)} purchase transactions.")
    
    # Populate the transactions_analytics table based on the matching.
    populate_transactions_analytics_from_matches(conn, matches)
    print("Matching complete. Check 'matched_transactions.log' for details and verify transactions_analytics table.")
    
    # Fetch historical ticker data.
    overall_start_date = datetime(2010, 1, 1)
    overall_end_date = datetime.utcnow() + timedelta(days=30)
    print("Overall Start Date:", overall_start_date)
    print("Overall End Date:", overall_end_date)
    ticker_histories = fetch_all_ticker_histories(conn, overall_start_date, overall_end_date)
    for ticker, hist in ticker_histories.items():
        print(f"{ticker}: {hist.shape[0]} rows")
    
    # Update the transactions_analytics table with price data.
    update_transactions_prices(conn, ticker_histories)
    print("Price data updated successfully.")
    
    # Update the transactions_analytics table with calculated percentage and net profit values.
    update_transactions_analytics_calculations(conn)
    print("Calculated values updated successfully.")