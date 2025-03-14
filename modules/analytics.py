# advanced_analytics.py

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from modules.utilis import average_amount  # Your function to convert amount ranges to a number
import logging
import time

logger = logging.getLogger("main_logger")

# -------------------------------------------------------------------
# TABLE INITIALIZATION
# -------------------------------------------------------------------
def init_analytics_table(conn):
    """
    Create an analytics table to store aggregated metrics per senator,
    including both basic and advanced analytics.
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
# HISTORICAL PRICE FETCHING
# -------------------------------------------------------------------
def get_price_at_date(ticker, target_date, max_offset=5, max_retries=3):
    ticker = ticker.lstrip('$')
    logger.debug(f"Fetching price for {ticker} on {target_date}")
    stock = yf.Ticker(ticker)
    retries = 0
    while retries < max_retries:
        start_date = target_date.strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=max_offset+1)).strftime("%Y-%m-%d")
        print(f"\nFetching data for {ticker} between {start_date} and {end_date}")
        try:
            hist = stock.history(start=start_date, end=end_date, interval="1d")
            time.sleep(1)  # Throttle after API call
            if hist.empty:
                return None
            for offset in range(max_offset + 1):
                check_date = (target_date + timedelta(days=offset)).strftime("%Y-%m-%d")
                if check_date in hist.index.strftime("%Y-%m-%d"):
                    print(hist.loc[check_date]["Close"])
                    return hist.loc[check_date]["Close"]
            return None
        except yf.exceptions.YFRateLimitError:
            print(f"Rate limit hit for ticker {ticker}. Sleeping for 5 seconds before retrying.")
            time.sleep(5)
            retries += 1
    return None

def fetch_all_ticker_histories(conn, overall_start_date, overall_end_date):
    """
    Fetch and return a dictionary mapping each unique ticker to its historical
    data (as a DataFrame) between overall_start_date and overall_end_date.
    """
    c = conn.cursor()
    # Adjust the query as needed to match your table schema.
    c.execute("""
        SELECT DISTINCT t.ticker
        FROM transactions t
        WHERE t.ticker <> '--'
    """)
    tickers = [row[0].lstrip('$') for row in c.fetchall()]
    
    ticker_histories = {}
    for ticker in tickers:
        print(f"Fetching history for {ticker} from {overall_start_date} to {overall_end_date}")
        stock = yf.Ticker(ticker)
        try:
            hist = stock.history(start=overall_start_date.strftime("%Y-%m-%d"),
                                   end=overall_end_date.strftime("%Y-%m-%d"),
                                   interval="1d")
            ticker_histories[ticker] = hist
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
        time.sleep(1)  # Throttle to avoid hitting the rate limit
    return ticker_histories

def get_price_from_history(ticker, target_date, ticker_histories, max_offset=5):
    """
    Return the closing price for a ticker from the pre-fetched history.
    If the price for target_date is missing (e.g. non-trading day),
    try forward up to max_offset days.
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
# PERFORMANCE CALCULATION FOR A TRANSACTION
# -------------------------------------------------------------------
def compute_transaction_performance(transaction, ticker_histories):
    """
    Compute performance metrics using pre-fetched ticker histories.
    """
    # Unpack the transaction. Assuming txn_date_str is in "MM/DD/YYYY" format.
    _, _, txn_date_str, _, ticker, _, _, _, _, _, _, _, _ = transaction
    purchase_date = datetime.strptime(txn_date_str, "%m/%d/%Y")
    today = datetime.utcnow()

    # Get purchase price
    purchase_price = get_price_from_history(ticker, purchase_date, ticker_histories)
    
    # Get current price (fetch only once)
    current_price = get_price_from_history(ticker, today, ticker_histories)
    
    # For 7-day price: if target date is in the future, use current price.
    target_7d = purchase_date + timedelta(days=7)
    price_7d = (current_price if target_7d > today 
                else get_price_from_history(ticker, target_7d, ticker_histories))
    
    # For 30-day price: same logic as 7-day.
    target_30d = purchase_date + timedelta(days=30)
    price_30d = (current_price if target_30d > today 
                 else get_price_from_history(ticker, target_30d, ticker_histories))
    
    def calc_perf(current):
        if purchase_price and purchase_price != 0 and current is not None:
            return ((current - purchase_price) / purchase_price) * 100
        return None
    
    return {
        "purchase_price": purchase_price,
        "price_7d": price_7d,
        "price_30d": price_30d,
        "current_price": current_price,
        "perf_7d": calc_perf(price_7d),
        "perf_30d": calc_perf(price_30d),
        "perf_current": calc_perf(current_price)
    }




# -------------------------------------------------------------------
# ADVANCED AGGREGATION: BASIC + PERFORMANCE & ACCURACY
# -------------------------------------------------------------------

def get_basic_analytics(conn):
    """
    Calculate basic analytics for each senator based on transactions.
    Returns a dictionary where keys are senator_ids and values are aggregated metrics.
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

    basic = {}  # key: senator_id, value: dict of basic aggregated metrics
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
    Calculate advanced metrics for open transactions.
    Returns a dictionary with senator_id as key and advanced metrics as value.
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
        # Build a transaction tuple for performance calculation.
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
                "total_net_profit": 0  # Placeholder for future calculation.
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
    Combine basic and advanced metrics and upsert them into the analytics table.
    """
    c = conn.cursor()
    for senator_id, basic_agg in basic.items():
        total_count = basic_agg["total_transaction_count"]
        avg_amount = (basic_agg["total_transaction_value"] / total_count) if total_count > 0 else 0

        # Set default advanced metrics.
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

def update_analytics(conn):
    start_time = time.time()
    basic = get_basic_analytics(conn)
    logger.info(f"Basic analytics fetched in {time.time() - start_time:.2f} seconds.")

    # Define overall date range.
    # You can compute overall_start_date as the earliest transaction date from your DB,
    # but here we'll hardcode it for illustration.
    overall_start_date = datetime(2010, 1, 1)
    overall_end_date = datetime.utcnow() + timedelta(days=30)
    
    # Fetch all ticker histories once.
    ticker_histories = fetch_all_ticker_histories(conn, overall_start_date, overall_end_date)
    
    # Pass the ticker_histories into advanced metrics.
    advanced = get_advanced_metrics(conn, ticker_histories)
    logger.info(f"Advanced analytics fetched in {time.time() - start_time:.2f} seconds.")

    upsert_analytics(conn, basic, advanced)
    logger.info(f"Analytics updated in {time.time() - start_time:.2f} seconds.")
    logger.info("Analytics table updated successfully.")
