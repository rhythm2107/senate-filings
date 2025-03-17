import sqlite3

def get_senators():
    """
    Returns a list of (senator_id, canonical_full_name, state, party),
    sorted by canonical_full_name.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT senator_id, canonical_full_name, state, party
        FROM senators
        ORDER BY canonical_full_name
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_matching_senators(partial_name: str) -> list[str]:
    """
    Query up to 25 senator names matching partial_name. We only filter out
    if total_value is NULL. (Or you can remove that filter entirely if you like.)
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT s.canonical_full_name
        FROM senators s
        JOIN analytics a ON a.senator_id = s.senator_id
        WHERE s.canonical_full_name LIKE ?
          AND a.total_value IS NOT NULL
        ORDER BY s.canonical_full_name
        LIMIT 25
    """, (f"%{partial_name}%",))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_senator_analytics(name: str):
    """
    Return the same 21 columns. If some are NULL, we won't block the entire row.
    We'll do row-based handling in the embed-building function.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT
            a.total_transaction_count,
            a.total_purchase_count,
            a.total_exchange_count,
            a.total_sale_count,
            a.total_stock_transactions,
            a.total_other_transactions,
            a.count_ownership_child,
            a.count_ownership_dependent_child,
            a.count_ownership_joint,
            a.count_ownership_self,
            a.count_ownership_spouse,
            a.total_transaction_value,
            a.average_transaction_amount,
            a.avg_perf_7d,
            a.avg_perf_30d,
            a.avg_perf_current,
            a.accuracy_7d,
            a.accuracy_30d,
            a.accuracy_current,
            a.total_net_profit,
            a.total_value
          FROM analytics AS a
          JOIN senators AS s ON s.senator_id = a.senator_id
         WHERE s.canonical_full_name = ?
    """, (name,))
    row = c.fetchone()
    conn.close()
    return row  # This can contain NULL in some columns.

def get_party_analytics(party_name: str):
    """
    Returns a row from analytics_party for the given party name,
    or None if not found. Each row is a 21-column tuple.
    """
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("""
        SELECT 
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
            total_net_profit,
            total_value
        FROM analytics_party
        WHERE party = ?
    """, (party_name,))
    row = c.fetchone()
    conn.close()
    return row  # None if not found, or a tuple with 21 columns

