import sqlite3
import time
from modules.db_helper import init_analytics_party_table

def populate_analytics_party(conn):
    """
    Aggregates the analytics data for each party by joining the analytics table
    with the senators table (to get party information). The aggregation sums up
    count and sum fields, and averages the average and performance metrics.
    The aggregated data is then inserted into (or updated in) the analytics_party table.
    """
    c = conn.cursor()
    
    # Aggregate analytics per party by joining with senators on senator_id.
    c.execute("""
        SELECT s.party,
               SUM(a.total_transaction_count) AS total_transaction_count,
               SUM(a.total_purchase_count) AS total_purchase_count,
               SUM(a.total_exchange_count) AS total_exchange_count,
               SUM(a.total_sale_count) AS total_sale_count,
               SUM(a.total_stock_transactions) AS total_stock_transactions,
               SUM(a.total_other_transactions) AS total_other_transactions,
               SUM(a.count_ownership_child) AS count_ownership_child,
               SUM(a.count_ownership_dependent_child) AS count_ownership_dependent_child,
               SUM(a.count_ownership_joint) AS count_ownership_joint,
               SUM(a.count_ownership_self) AS count_ownership_self,
               SUM(a.count_ownership_spouse) AS count_ownership_spouse,
               SUM(a.total_transaction_value) AS total_transaction_value,
               AVG(a.average_transaction_amount) AS average_transaction_amount,
               AVG(a.avg_perf_7d) AS avg_perf_7d,
               AVG(a.avg_perf_30d) AS avg_perf_30d,
               AVG(a.avg_perf_current) AS avg_perf_current,
               AVG(a.accuracy_7d) AS accuracy_7d,
               AVG(a.accuracy_30d) AS accuracy_30d,
               AVG(a.accuracy_current) AS accuracy_current,
               SUM(a.total_net_profit) AS total_net_profit,
               SUM(a.total_value) AS total_value
        FROM analytics a
        JOIN senators s ON a.senator_id = s.senator_id
        GROUP BY s.party
    """)
    
    rows = c.fetchall()
    
    # Insert aggregated data into analytics_party table.
    for row in rows:
        (party, total_transaction_count, total_purchase_count, total_exchange_count,
         total_sale_count, total_stock_transactions, total_other_transactions,
         count_ownership_child, count_ownership_dependent_child, count_ownership_joint,
         count_ownership_self, count_ownership_spouse, total_transaction_value,
         average_transaction_amount, avg_perf_7d, avg_perf_30d, avg_perf_current,
         accuracy_7d, accuracy_30d, accuracy_current, total_net_profit, total_value) = row
        
        c.execute("""
            INSERT INTO analytics_party (
                party,
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(party) DO UPDATE SET
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
                total_net_profit = excluded.total_net_profit,
                total_value = excluded.total_value
        """, (
            party,
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
        ))
    
    conn.commit()
    print("analytics_party table populated successfully.")

def update_party_analytics(conn):
    """
    Updates the analytics_party table with the latest analytics data.
    """
    init_analytics_party_table(conn)
    time.sleep(1)
    populate_analytics_party(conn)
    print("Party analytics updated successfully.")