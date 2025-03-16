import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from modules.utilis import average_amount, get_ignore_tickers
import logging
import time

logger = logging.getLogger("main_logger")

# -------------------------------------------------------------------
# TABLE INITIALIZATION FOR AGGREGATED ANALYTICS
# -------------------------------------------------------------------
def init_analytics_table(conn):
    """
    Create an analytics table to store aggregated metrics per senator.
    """
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            senator_id INTEGER PRIMARY KEY,
            total_transaction_count INTEGER,
            total_purchase_count INTEGER,
            total_exchange_count INTEGER,
            total_sale_count INTEGER,
            total_stock_transactions INTEGER,
            total_other_transactions INTEGER,
            count_ownership_child INTEGER,
            count_ownership_dependent_child INTEGER,
            count_ownership_joint INTEGER,
            count_ownership_self INTEGER,
            count_ownership_spouse INTEGER,
            total_transaction_value INTEGER,
            average_transaction_amount REAL,
            avg_perf_7d REAL,
            avg_perf_30d REAL,
            avg_perf_current REAL,
            accuracy_7d REAL,
            accuracy_30d REAL,
            accuracy_current REAL,
            total_net_profit REAL
        )
    ''')
    conn.commit()
    logger.debug("Analytics table created or verified.")

# -------------------------------------------------------------------
# TABLE INITIALIZATION FOR TRANSACTION ANALYTICS
# -------------------------------------------------------------------
def init_transactions_analytics_table(conn):
    """
    Create a table to store detailed transaction analytics.
    """
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions_analytics (
            ptr_id TEXT PRIMARY KEY,
            senator_id INTEGER,
            transaction_number INTEGER,
            transaction_date TEXT,
            ticker TEXT,
            type TEXT,
            amount TEXT,
            asset_type TEXT,
            status TEXT,              -- 'closed' if a matching sale is found; otherwise 'open'
            estimated_invested REAL,  -- average of the amount range
            price_purchase REAL,      -- price on purchase date
            price_7d REAL,            -- price 7 days after purchase
            price_30d REAL,           -- price 30 days after purchase
            price_closing REAL,       -- price on sale date if closed; NULL otherwise
            price_today REAL,         -- price today if open; NULL otherwise
            gain_7d REAL,             -- % gain at 7 days
            gain_30d REAL,            -- % gain at 30 days
            gain_closing REAL,        -- % gain on day of closing if closed; NULL otherwise
            gain_today REAL           -- % gain today if open; NULL otherwise
        )
    ''')
    conn.commit()
    logger.debug("transactions_analytics table created or verified.")

# -------------------------------------------------------------------
# HISTORICAL PRICE FETCHING FUNCTIONS
# -------------------------------------------------------------------
def get_price_at_date(ticker, target_date, max_offset=5, max_retries=3):
    ticker = ticker.lstrip('$')
    logger.debug(f"Fetching price for {ticker} on {target_date}")
    stock = yf.Ticker(ticker)
    retries = 0
    while retries < max_retries:
        start_date = target_date.strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=max_offset+1)).strftime("%Y-%m-%d")
        try:
            hist = stock.history(start=start_date, end=end_date, interval="1d", actions=False)
            time.sleep(1)
            if hist.empty:
                return None
            for offset in range(max_offset + 1):
                check_date = (target_date + timedelta(days=offset)).strftime("%Y-%m-%d")
                if check_date in hist.index.strftime("%Y-%m-%d"):
                    return hist.loc[check_date]["Close"]
            return None
        except yf.exceptions.YFRateLimitError:
            logger.warning(f"Rate limit hit for {ticker}. Sleeping for 5 seconds before retrying.")
            time.sleep(5)
            retries += 1
    return None

def fetch_all_ticker_histories(conn, overall_start_date, overall_end_date, ignore_file="resources/ignore_tickers.txt"):
    """
    Fetch a dictionary mapping each unique ticker to its historical data
    between overall_start_date and overall_end_date.
    Tickers in the ignore file are skipped.
    """
    c = conn.cursor()   
    c.execute("""
        SELECT DISTINCT t.ticker
        FROM transactions t
        WHERE t.ticker <> '--'
    """)
    tickers = [row[0].lstrip('$') for row in c.fetchall()]
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
    Return the closing price for a ticker from the pre-fetched history.
    If not available for target_date, try up to max_offset days forward.
    """
    ticker = ticker.lstrip('$')
    if ticker not in ticker_histories:
        return None
    hist = ticker_histories[ticker]
    available_dates = [d.strftime("%Y-%m-%d") for d in hist.index]
    for offset in range(max_offset + 1):
        check_date = (target_date + timedelta(days=offset)).strftime("%Y-%m-%d")
        if check_date in available_dates:
            return hist.loc[check_date]["Close"]
    return None

# -------------------------------------------------------------------
# PERFORMANCE CALCULATION
# -------------------------------------------------------------------
def compute_transaction_performance(transaction, ticker_histories):
    """
    Compute performance metrics using pre-fetched ticker histories.
    
    Supports transaction tuple lengths of 6, 8, or 13.
    
    For a 13-tuple (as constructed in get_advanced_metrics):
       (ptr_id, txn_num, transaction_date, None, ticker, None, None, None, "purchase", amount_str, None, None, None)
       -> We need: txn_date_str from index 2, ticker from index 4, amount_str from index 9.
       
    For an 8-tuple:
       (senator_id, ptr_id, transaction_number, transaction_date, ticker, type, amount, asset_type)
       -> We need: txn_date_str from index 3, ticker from index 4, amount_str from index 6.
       
    For a 6-tuple:
       (senator_id, ptr_id, transaction_number, transaction_date, ticker, amount)
       -> We need: txn_date_str from index 3, ticker from index 4, amount_str from index 5.
    """
    if len(transaction) == 13:
        _, _, txn_date_str, _, ticker, _, _, _, _, amount_str, _, _, _ = transaction
    elif len(transaction) == 8:
        _, _, _, txn_date_str, ticker, _, amount_str, _ = transaction
    elif len(transaction) == 6:
        _, _, _, txn_date_str, ticker, amount_str = transaction
    else:
        raise ValueError(f"Unexpected transaction tuple length: {len(transaction)}")
    
    # Convert transaction date (expected in MM/DD/YYYY format) to a Python date object.
    purchase_date = datetime.strptime(txn_date_str, "%m/%d/%Y")
    today = datetime.utcnow()
    
    # Fetch prices from history.
    price_purchase = get_price_from_history(ticker, purchase_date, ticker_histories)
    current_price = get_price_from_history(ticker, today, ticker_histories)
    
    target_7d = purchase_date + timedelta(days=7)
    price_7d = current_price if target_7d > today else get_price_from_history(ticker, target_7d, ticker_histories)
    
    target_30d = purchase_date + timedelta(days=30)
    price_30d = current_price if target_30d > today else get_price_from_history(ticker, target_30d, ticker_histories)
    
    def calc_perf(current):
        if price_purchase and price_purchase != 0 and current is not None:
            return ((current - price_purchase) / price_purchase) * 100
        return None
    
    return {
        "purchase_price": price_purchase,
        "price_7d": price_7d,
        "price_30d": price_30d,
        "current_price": current_price,
        "perf_7d": calc_perf(price_7d),
        "perf_30d": calc_perf(price_30d),
        "perf_current": calc_perf(current_price)
    }




# -------------------------------------------------------------------
# BASIC AND ADVANCED ANALYTICS FUNCTIONS (Existing)
# -------------------------------------------------------------------
def get_basic_analytics(conn):
    """
    Calculate basic aggregated metrics per senator from transactions.
    """
    c = conn.cursor()
    query = '''
        SELECT f.senator_id, t.type, t.asset_type, t.owner, t.amount
        FROM transactions t
        JOIN filings f ON t.ptr_id = f.ptr_id
        WHERE f.senator_id IS NOT NULL
          AND LOWER(t.asset_type) = 'stock'
          AND t.ticker <> '--'
    '''
    c.execute(query)
    rows = c.fetchall()
    basic = {}
    for row in rows:
        senator_id, txn_type, asset_type, owner, amount_str = row
        if senator_id not in basic:
            basic[senator_id] = {
                "total_transaction_count": 0,
                "total_purchase_count": 0,
                "total_exchange_count": 0,
                "total_sale_count": 0,
                "total_stock_transactions": 0,
                "total_other_transactions": 0,
                "count_ownership_child": 0,
                "count_ownership_dependent_child": 0,
                "count_ownership_joint": 0,
                "count_ownership_self": 0,
                "count_ownership_spouse": 0,
                "total_transaction_value": 0
            }
        agg = basic[senator_id]
        agg["total_transaction_count"] += 1
        txn_type_lower = txn_type.lower().strip()
        if "purchase" in txn_type_lower:
            agg["total_purchase_count"] += 1
        elif "exchange" in txn_type_lower:
            agg["total_exchange_count"] += 1
        elif "sale" in txn_type_lower:
            agg["total_sale_count"] += 1
        agg["total_stock_transactions"] += 1
        owner_lower = owner.lower().strip()
        if owner_lower == "child":
            agg["count_ownership_child"] += 1
        elif owner_lower in ["dependant child", "dependent child"]:
            agg["count_ownership_dependent_child"] += 1
        elif owner_lower == "joint":
            agg["count_ownership_joint"] += 1
        elif owner_lower == "self":
            agg["count_ownership_self"] += 1
        elif owner_lower == "spouse":
            agg["count_ownership_spouse"] += 1
        numeric_value = average_amount(amount_str)
        if numeric_value is not None:
            agg["total_transaction_value"] += numeric_value
    return basic

def get_advanced_metrics(conn, ticker_histories):
    """
    Calculate advanced performance metrics for open purchase transactions.
    """
    c = conn.cursor()
    c.execute("""
        SELECT f.senator_id, t.ptr_id, t.transaction_number, t.transaction_date, t.ticker, t.amount
        FROM transactions t
        JOIN filings f ON t.ptr_id = f.ptr_id
        WHERE LOWER(t.type) LIKE '%purchase%'
          AND t.asset_type IS NOT NULL
          AND LOWER(t.asset_type) = 'stock'
          AND t.ticker <> '--'
          AND NOT EXISTS (
              SELECT 1 FROM transactions ts
              JOIN filings f2 ON ts.ptr_id = f2.ptr_id
              WHERE LOWER(ts.type) LIKE '%sale%'
                AND ts.ticker = t.ticker
                AND ts.transaction_date > t.transaction_date
                AND f2.senator_id = f.senator_id
          )
    """)
    rows = c.fetchall()
    advanced = {}
    for row in rows:
        senator_id, ptr_id, txn_num, txn_date, ticker, amount_str = row
        transaction = (ptr_id, txn_num, txn_date, None, ticker, None, None, None, "purchase", amount_str, None, None, None)
        perf = compute_transaction_performance(transaction, ticker_histories)
        if perf.get("purchase_price") is None:
            continue
        if senator_id not in advanced:
            advanced[senator_id] = {
                "total_open": 0,
                "sum_perf_7d": 0,
                "sum_perf_30d": 0,
                "sum_perf_current": 0,
                "count_perf_7d": 0,
                "count_perf_30d": 0,
                "count_perf_current": 0,
                "positive_7d": 0,
                "positive_30d": 0,
                "positive_current": 0,
                "total_net_profit": 0
            }
        adv = advanced[senator_id]
        adv["total_open"] += 1
        for horizon in ["7d", "30d", "current"]:
            key = f"perf_{horizon}"
            if perf.get(key) is not None:
                adv[f"sum_{key}"] += perf[key]
                adv[f"count_{key}"] += 1
                if perf[key] > 0:
                    adv[f"positive_{horizon}"] += 1
    return advanced

def upsert_analytics(conn, basic, advanced):
    """
    Combine basic and advanced metrics and upsert into the analytics table.
    """
    c = conn.cursor()
    for senator_id, basic_agg in basic.items():
        total_count = basic_agg["total_transaction_count"]
        avg_amount = (basic_agg["total_transaction_value"] / total_count) if total_count > 0 else 0
        avg_perf_7d = avg_perf_30d = avg_perf_current = 0
        accuracy_7d = accuracy_30d = accuracy_current = 0
        if senator_id in advanced and advanced[senator_id]["total_open"] > 0:
            adv = advanced[senator_id]
            if adv["count_perf_7d"] > 0:
                avg_perf_7d = adv["sum_perf_7d"] / adv["count_perf_7d"]
                accuracy_7d = (adv["positive_7d"] / adv["total_open"]) * 100
            if adv["count_perf_30d"] > 0:
                avg_perf_30d = adv["sum_perf_30d"] / adv["count_perf_30d"]
                accuracy_30d = (adv["positive_30d"] / adv["total_open"]) * 100
            if adv["count_perf_current"] > 0:
                avg_perf_current = adv["sum_perf_current"] / adv["count_perf_current"]
                accuracy_current = (adv["positive_current"] / adv["total_open"]) * 100
        c.execute('''
            INSERT INTO analytics (
                senator_id,
                total_transaction_count,
                total_purchase_count,
                total_exchange_count,
                total_sale_count,
                total_stock_transactions,
                total_other_transactions,
                count_ownership_child,
                count_ownership_dependent_child,
                count_ownership_joint,
                count_ownership_self,
                count_ownership_spouse,
                total_transaction_value,
                average_transaction_amount,
                avg_perf_7d,
                avg_perf_30d,
                avg_perf_current,
                accuracy_7d,
                accuracy_30d,
                accuracy_current,
                total_net_profit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(senator_id) DO UPDATE SET
                total_transaction_count = excluded.total_transaction_count,
                total_purchase_count = excluded.total_purchase_count,
                total_exchange_count = excluded.total_exchange_count,
                total_sale_count = excluded.total_sale_count,
                total_stock_transactions = excluded.total_stock_transactions,
                total_other_transactions = excluded.total_other_transactions,
                count_ownership_child = excluded.count_ownership_child,
                count_ownership_dependent_child = excluded.count_ownership_dependent_child,
                count_ownership_joint = excluded.count_ownership_joint,
                count_ownership_self = excluded.count_ownership_self,
                count_ownership_spouse = excluded.count_ownership_spouse,
                total_transaction_value = excluded.total_transaction_value,
                average_transaction_amount = excluded.average_transaction_amount,
                avg_perf_7d = excluded.avg_perf_7d,
                avg_perf_30d = excluded.avg_perf_30d,
                avg_perf_current = excluded.avg_perf_current,
                accuracy_7d = excluded.accuracy_7d,
                accuracy_30d = excluded.accuracy_30d,
                accuracy_current = excluded.accuracy_current,
                total_net_profit = excluded.total_net_profit
        ''', (
            senator_id,
            total_count,
            basic_agg["total_purchase_count"],
            basic_agg["total_exchange_count"],
            basic_agg["total_sale_count"],
            basic_agg["total_stock_transactions"],
            basic_agg["total_other_transactions"],
            basic_agg["count_ownership_child"],
            basic_agg["count_ownership_dependent_child"],
            basic_agg["count_ownership_joint"],
            basic_agg["count_ownership_self"],
            basic_agg["count_ownership_spouse"],
            basic_agg["total_transaction_value"],
            avg_amount,
            avg_perf_7d,
            avg_perf_30d,
            avg_perf_current,
            accuracy_7d,
            accuracy_30d,
            accuracy_current,
            0  # total_net_profit placeholder
        ))
    conn.commit()
    logger.info("Analytics table updated successfully.")

# -------------------------------------------------------------------
# POPULATE TRANSACTIONS_ANALYTICS TABLE
# -------------------------------------------------------------------
def populate_transactions_analytics(conn, ticker_histories):
    """
    For each purchase transaction (Stock) in transactions,
    determine if it's closed (if a sale exists later) and compute additional fields.
    Populates the transactions_analytics table with:
      - status: 'closed' if a matching sale is found, else 'open'
      - estimated_invested: average of the amount range
      - price_purchase: price on purchase date (from historical data)
      - price_7d: price 7 days after purchase
      - price_30d: price 30 days after purchase
      - price_closing: price on sale date if closed; else NULL
      - price_today: price today if open; else NULL
      - gain_7d, gain_30d, gain_closing, gain_today: corresponding percentage gains
    """
    c = conn.cursor()
    c.execute("""
       SELECT f.senator_id, t.ptr_id, t.transaction_number, t.transaction_date, 
              t.ticker, t.type, t.amount, t.asset_type
       FROM transactions t
       JOIN filings f ON t.ptr_id = f.ptr_id
       WHERE LOWER(t.type) LIKE '%purchase%'
         AND LOWER(t.asset_type) = 'stock'
         AND t.ticker <> '--'
       ORDER BY t.transaction_date ASC
    """)
    purchases = c.fetchall()
    today = datetime.utcnow()
    
    for purchase in purchases:
        senator_id, ptr_id, txn_num, txn_date, ticker, tx_type, amount_str, asset_type = purchase
        try:
            purchase_date = datetime.strptime(txn_date, "%m/%d/%Y")
        except Exception as e:
            logger.error(f"Error converting purchase date '{txn_date}' for ptr_id {ptr_id}: {e}")
            continue

        estimated_invested = average_amount(amount_str)
        
        # Compute performance metrics (prices, % gains) for this purchase.
        perf = compute_transaction_performance(purchase, ticker_histories)
        price_purchase = perf.get("purchase_price")
        price_7d = perf.get("price_7d")
        price_30d = perf.get("price_30d")
        
        # Default values assume open transaction.
        status = "open"
        price_closing = None
        gain_closing = None
        price_today = perf.get("current_price")
        gain_today = perf.get("perf_current")
        
        # --- Modified Sale Lookup ---
        # Instead of filtering by date in SQL, get all sale transactions for this ticker and senator.
        c.execute("""
            SELECT s.transaction_date
            FROM transactions s
            JOIN filings fs ON s.ptr_id = fs.ptr_id
            WHERE s.ticker = ?
              AND fs.senator_id = ?
              AND LOWER(s.type) LIKE '%sale%'
              AND LOWER(s.asset_type) = 'stock'
              AND s.ticker <> '--'
            ORDER BY CAST(substr(s.transaction_date,7,4) || '-' ||
                          substr(s.transaction_date,1,2) || '-' ||
                          substr(s.transaction_date,4,2) AS DATE) ASC
        """, (ticker, senator_id))
        sales = c.fetchall()
        logger.debug(f"For ptr_id {ptr_id} (purchase date {txn_date}), found {len(sales)} sale candidate(s) for ticker {ticker}.")
        
        # Now, in Python, filter the candidate sales to find the first sale that occurs after purchase_date.
        matching_sale = None
        for sale in sales:
            sale_date_str = sale[0]
            try:
                sale_date = datetime.strptime(sale_date_str, "%m/%d/%Y")
            except Exception as e:
                logger.error(f"Error converting sale date '{sale_date_str}' for ptr_id {ptr_id}: {e}")
                continue
            if sale_date > purchase_date:
                matching_sale = sale_date
                break
        
        if matching_sale:
            status = "closed"
            price_closing = get_price_from_history(ticker, matching_sale, ticker_histories)
            if price_purchase and price_closing:
                gain_closing = ((price_closing - price_purchase) / price_purchase) * 100
        else:
            logger.debug(f"No matching sale (sale date > purchase date) found for ptr_id {ptr_id}.")
        
        gain_7d = ((price_7d - price_purchase) / price_purchase * 100) if price_purchase and price_7d else None
        gain_30d = ((price_30d - price_purchase) / price_purchase * 100) if price_purchase and price_30d else None
        
        analytics_data = (
            ptr_id,
            senator_id,
            txn_num,
            txn_date,
            ticker,
            tx_type,
            amount_str,
            asset_type,
            status,
            estimated_invested,
            price_purchase,
            price_7d,
            price_30d,
            price_closing,
            price_today if status == "open" else None,
            gain_7d,
            gain_30d,
            gain_closing,
            gain_today if status == "open" else None
        )
        
        c.execute("""
            INSERT OR REPLACE INTO transactions_analytics (
                ptr_id,
                senator_id,
                transaction_number,
                transaction_date,
                ticker,
                type,
                amount,
                asset_type,
                status,
                estimated_invested,
                price_purchase,
                price_7d,
                price_30d,
                price_closing,
                price_today,
                gain_7d,
                gain_30d,
                gain_closing,
                gain_today
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, analytics_data)
    conn.commit()
    logger.info("transactions_analytics table populated successfully.")


# -------------------------------------------------------------------
# MAIN UPDATE FUNCTION
# -------------------------------------------------------------------
def update_analytics(conn):
    start_time = time.time()
    basic = get_basic_analytics(conn)
    logger.info(f"Basic analytics fetched in {time.time() - start_time:.2f} seconds.")

    overall_start_date = datetime(2010, 1, 1)
    overall_end_date = datetime.utcnow() + timedelta(days=30)
    
    ticker_histories = fetch_all_ticker_histories(conn, overall_start_date, overall_end_date)
    
    advanced = get_advanced_metrics(conn, ticker_histories)
    logger.info(f"Advanced analytics fetched in {time.time() - start_time:.2f} seconds.")

    upsert_analytics(conn, basic, advanced)
    logger.info(f"Analytics updated in {time.time() - start_time:.2f} seconds.")
    logger.info("Analytics table updated successfully.")

    populate_transactions_analytics(conn, ticker_histories)
    logger.info(f"Transactions analytics updated in {time.time() - start_time:.2f} seconds.")

# -------------------------------------------------------------------
# Example Usage
# -------------------------------------------------------------------
if __name__ == "__main__":
    conn = sqlite3.connect("your_database.db")
    init_analytics_table(conn)
    init_transactions_analytics_table(conn)
    update_analytics(conn)
    print("Analytics and transactions analytics updated successfully.")
