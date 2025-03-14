import yfinance as yf
from datetime import datetime, timedelta

# BASIC ANALYTICS FUNCTIONS
def update_analytics(conn):
    """
    Calculate analytics for each senator based on transactions and update the analytics table.
    Since the transactions table does not contain senator_id directly, we join with filings.
    """
    c = conn.cursor()
    # Clear the analytics table so we can recompute all values:
    c.execute("DELETE FROM analytics")
    conn.commit()

    # Join transactions with filings to get senator_id from filings.
    query = '''
        SELECT f.senator_id, t.type, t.asset_type, t.owner, t.amount
        FROM transactions t
        JOIN filings f ON t.ptr_id = f.ptr_id
        WHERE f.senator_id IS NOT NULL
    '''
    c.execute(query)
    rows = c.fetchall()

    # Aggregate metrics per senator
    analytics = {}  # key: senator_id, value: dict of aggregated metrics
    for row in rows:
        senator_id, txn_type, asset_type, owner, amount_str = row
        if senator_id not in analytics:
            analytics[senator_id] = {
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
        agg = analytics[senator_id]
        agg["total_transaction_count"] += 1

        # Count transaction types (assume txn_type contains keywords)
        txn_type_lower = txn_type.lower().strip()
        if "purchase" in txn_type_lower:
            agg["total_purchase_count"] += 1
        elif "exchange" in txn_type_lower:
            agg["total_exchange_count"] += 1
        elif "sale" in txn_type_lower:
            agg["total_sale_count"] += 1

        # Asset type: if asset_type equals "Stock" (case-insensitive), count as stock; else, others.
        if asset_type.lower().strip() == "stock":
            agg["total_stock_transactions"] += 1
        else:
            agg["total_other_transactions"] += 1

        # Ownership counts: assuming owner field is exactly one of these strings.
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

        # Use the utility function to get the average numeric value from the amount range.
        from modules.utilis import average_amount
        numeric_value = average_amount(amount_str)
        if numeric_value is not None:
            agg["total_transaction_value"] += numeric_value

    # Insert aggregated data into the analytics table
    for senator_id, agg in analytics.items():
        total_count = agg["total_transaction_count"]
        avg_amount = (agg["total_transaction_value"] / total_count) if total_count > 0 else 0
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
                average_transaction_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            senator_id,
            total_count,
            agg["total_purchase_count"],
            agg["total_exchange_count"],
            agg["total_sale_count"],
            agg["total_stock_transactions"],
            agg["total_other_transactions"],
            agg["count_ownership_child"],
            agg["count_ownership_dependent_child"],
            agg["count_ownership_joint"],
            agg["count_ownership_self"],
            agg["count_ownership_spouse"],
            agg["total_transaction_value"],
            avg_amount
        ))
    conn.commit()

# ADVANCED ANALYTICS FUNCTIONS
def get_price_at_date(ticker, target_date):
    """
    Given a ticker and a target_date (datetime), return the closing price on that date.
    If no data is available (e.g., a weekend), try the next available date.
    """
    # Format target_date as string (YYYY-MM-DD) for the API call.
    start_date = target_date.strftime("%Y-%m-%d")
    # End date is target_date + 1 day
    end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    if not hist.empty:
        # .iloc[0] accesses the first row in the Series of closing prices.
        return hist["Close"].iloc[0]
    else:
        return None


def compute_transaction_performance(transaction, price_fetcher=get_price_at_date):
    """
    Given a transaction tuple (assumed to be:
      (ptr_id, txn_num, txn_date, owner, ticker, asset_name,
       additional_info, asset_type, txn_type, amount, comment, filing_date, name))
    where txn_date is the purchase date (as "MM/DD/YYYY"),
    fetch the historical prices at 7 days, 30 days, and now.
    
    Returns a dictionary with:
      - purchase_price
      - price_7d, price_30d, current_price
      - perf_7d, perf_30d, perf_current (in percentages)
    """
    # Unpack needed fields
    _, _, txn_date_str, _, ticker, _, _, _, _, _, _, _, _ = transaction
    # Parse using MM/DD/YYYY format
    purchase_date = datetime.strptime(txn_date_str, "%m/%d/%Y")
    
    purchase_price = price_fetcher(ticker, purchase_date)
    price_7d = price_fetcher(ticker, purchase_date + timedelta(days=7))
    price_30d = price_fetcher(ticker, purchase_date + timedelta(days=30))
    current_price = price_fetcher(ticker, datetime.utcnow())
    
    def calc_perf(current):
        if purchase_price and purchase_price != 0 and current is not None:
            return ((current - purchase_price) / purchase_price) * 100
        else:
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


def match_transactions(conn):
    """
    For each purchase transaction, find the earliest matching sale transaction (for the same ticker)
    that occurred after the purchase, and belonging to the same senator.
    Compute profit in dollars and percent.
    Returns a list of dictionaries with matched data.
    """
    c = conn.cursor()
    # Fetch purchase transactions (from transactions joined with filings to get senator_id)
    c.execute("""
        SELECT f.senator_id, t.ptr_id, t.transaction_number, t.transaction_date, t.ticker, t.amount
        FROM transactions t
        JOIN filings f ON t.ptr_id = f.ptr_id
        WHERE LOWER(t.type) LIKE '%purchase%'
    """)
    purchases = c.fetchall()
    matches = []
    
    from modules.utilis import average_amount  # assuming you have this function to compute an average value from a range
    for purchase in purchases:
        senator_id, p_ptr, p_txn, p_date, p_ticker, p_amount = purchase
        # Find earliest sale for the same ticker, where sale date > purchase date and sale belongs to the same senator.
        c.execute("""
            SELECT t.ptr_id, t.transaction_number, t.transaction_date, t.amount
            FROM transactions t
            JOIN filings f2 ON t.ptr_id = f2.ptr_id
            WHERE LOWER(t.type) LIKE '%sale%'
              AND t.ticker = ?
              AND t.transaction_date > ?
              AND f2.senator_id = ?
            ORDER BY t.transaction_date ASC
            LIMIT 1
        """, (p_ticker, p_date, senator_id))
        sale = c.fetchone()
        if sale:
            s_ptr, s_txn, s_date, s_amount = sale
            buy_val = average_amount(p_amount)
            sell_val = average_amount(s_amount)
            if buy_val is not None and sell_val is not None:
                profit_amount = sell_val - buy_val
                profit_percentage = ((profit_amount) / buy_val * 100) if buy_val != 0 else None
            else:
                profit_amount = None
                profit_percentage = None
            matches.append({
                "senator_id": senator_id,
                "buy_ptr": p_ptr,
                "buy_txn": p_txn,
                "sell_ptr": s_ptr,
                "sell_txn": s_txn,
                "buy_date": p_date,
                "sell_date": s_date,
                "profit_percentage": profit_percentage,
                "profit_amount": profit_amount
            })
    return matches


def compute_accuracy_metrics(performance_results):
    """
    Given a list of performance result dictionaries along with senator_id,
    compute the accuracy per senator for each time horizon.
    Expected input: a list of tuples (senator_id, performance_dict)
    where performance_dict is the output of compute_transaction_performance.
    
    Returns a dict keyed by senator_id with accuracy percentages.
    """
    accuracy = {}
    for senator_id, perf in performance_results:
        if senator_id not in accuracy:
            accuracy[senator_id] = {"total": 0, "positive_7d": 0, "positive_30d": 0, "positive_current": 0}
        accuracy[senator_id]["total"] += 1
        if perf.get("perf_7d") is not None and perf.get("perf_7d") > 0:
            accuracy[senator_id]["positive_7d"] += 1
        if perf.get("perf_30d") is not None and perf.get("perf_30d") > 0:
            accuracy[senator_id]["positive_30d"] += 1
        if perf.get("perf_current") is not None and perf.get("perf_current") > 0:
            accuracy[senator_id]["positive_current"] += 1
    
    # Compute percentages
    for senator_id, stats in accuracy.items():
        total = stats["total"]
        stats["accuracy_7d"] = (stats["positive_7d"] / total * 100) if total > 0 else 0
        stats["accuracy_30d"] = (stats["positive_30d"] / total * 100) if total > 0 else 0
        stats["accuracy_current"] = (stats["positive_current"] / total * 100) if total > 0 else 0
    return accuracy
