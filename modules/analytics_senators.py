import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from modules.utilis import average_amount, get_ignore_tickers
import logging
import time
from modules.db_helper import init_analytics_table

logger = logging.getLogger("main_logger")

def update_senators_analytics_right(conn):
    """
    Aggregates transaction analytics per senator using data from transactions_analytics
    and updates/inserts the results into the analytics table.
    
    The aggregated metrics calculated here are:
      - avg_perf_7d: average of the percent_7d values (skipping NULLs).
      - avg_perf_30d: average of the percent_30d values.
      - avg_perf_current: average of the percent_today values.
      - accuracy_7d: percentage of transactions with a positive percent_7d (of those that are not NULL).
      - accuracy_30d: same for percent_30d.
      - accuracy_current: same for percent_today.
      - total_net_profit: sum of the net_profit column.
      - total_value: sum of the current_value column.
      
    The following fields are set as placeholder NULL (None) and will be calculated separately:
      - total_transaction_count
      - total_purchase_count
      - total_exchange_count
      - total_sale_count
      - total_stock_transactions
      - total_other_transactions
      - count_ownership_child
      - count_ownership_dependent_child
      - count_ownership_joint
      - count_ownership_self
      - count_ownership_spouse
      - total_transaction_value
      - average_transaction_amount
      
    Senator IDs are fetched from the "senators" table.
    """
    c = conn.cursor()
    
    # Fetch all senator IDs.
    c.execute("SELECT senator_id FROM senators")
    senator_ids = [row[0] for row in c.fetchall()]
    
    for senator_id in senator_ids:
        # Retrieve only the necessary columns for performance and profit calculations.
        c.execute("""
            SELECT percent_7d, percent_30d, percent_today, net_profit, current_value
            FROM transactions_analytics
            WHERE senator_id = ?
        """, (senator_id,))
        rows = c.fetchall()
        
        if not rows:
            continue
        
        # Initialize counters and accumulators.
        sum_perf_7d = 0.0
        count_perf_7d = 0
        positive_7d = 0
        
        sum_perf_30d = 0.0
        count_perf_30d = 0
        positive_30d = 0
        
        sum_perf_current = 0.0
        count_perf_current = 0
        positive_current = 0
        
        total_net_profit = 0.0
        total_current_value = 0.0
        
        # Process each transaction row.
        for row in rows:
            # row: (percent_7d, percent_30d, percent_today, net_profit, current_value)
            p7, p30, pcurrent, net_profit, current_val = row
            if p7 is not None:
                sum_perf_7d += p7
                count_perf_7d += 1
                if p7 > 0:
                    positive_7d += 1
            if p30 is not None:
                sum_perf_30d += p30
                count_perf_30d += 1
                if p30 > 0:
                    positive_30d += 1
            if pcurrent is not None:
                sum_perf_current += pcurrent
                count_perf_current += 1
                if pcurrent > 0:
                    positive_current += 1
            if net_profit is not None:
                total_net_profit += net_profit
            if current_val is not None:
                total_current_value += current_val
        
        # Compute averages and accuracies.
        avg_perf_7d = sum_perf_7d / count_perf_7d if count_perf_7d else None
        avg_perf_30d = sum_perf_30d / count_perf_30d if count_perf_30d else None
        avg_perf_current = sum_perf_current / count_perf_current if count_perf_current else None
        
        accuracy_7d = (positive_7d / count_perf_7d * 100) if count_perf_7d else None
        accuracy_30d = (positive_30d / count_perf_30d * 100) if count_perf_30d else None
        accuracy_current = (positive_current / count_perf_current * 100) if count_perf_current else None
        
        # Insert or update the analytics table.
        c.execute("""
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
                total_net_profit,
                total_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                total_net_profit = excluded.total_net_profit,
                total_value = excluded.total_value
        """, (
            senator_id,
            None,  # total_transaction_count
            None,  # total_purchase_count
            None,  # total_exchange_count
            None,  # total_sale_count
            None,  # total_stock_transactions
            None,  # total_other_transactions
            None,  # count_ownership_child
            None,  # count_ownership_dependent_child
            None,  # count_ownership_joint
            None,  # count_ownership_self
            None,  # count_ownership_spouse
            None,  # total_transaction_value
            None,  # average_transaction_amount
            avg_perf_7d,
            avg_perf_30d,
            avg_perf_current,
            accuracy_7d,
            accuracy_30d,
            accuracy_current,
            total_net_profit,
            total_current_value
        ))
    conn.commit()
    print("Senators analytics updated successfully.")

def update_senators_analytics_left(conn):
    """
    Aggregates the left-side transaction analytics per senator by joining the
    transactions and filings tables, then updates/inserts the corresponding fields
    into the analytics table.
    
    The computed metrics are:
      - total_transaction_count: Total count of transactions performed by the senator.
      - total_purchase_count: Count of transactions with type in 
            ('Purchase', 'Sale', 'Sale (Full)', 'Sale (Partial)', 'Exchange').
      - total_exchange_count: Count of transactions where type is 'Exchange'.
      - total_sale_count: Count of transactions where type is one of the sale types
            ('Sale', 'Sale (Full)', 'Sale (Partial)').
      - total_stock_transactions: Count of transactions where asset_type is "Stock".
      - total_other_transactions: Count of transactions where asset_type is not "Stock".
      - count_ownership_child: Count of transactions where owner equals "Child".
      - count_ownership_dependent_child: Count where owner equals "Dependent Child".
      - count_ownership_joint: Count where owner equals "Joint".
      - count_ownership_self: Count where owner equals "Self".
      - count_ownership_spouse: Count where owner equals "Spouse".
      - total_transaction_value: Sum of the average amounts extracted from the 'amount'
            field (using the average_amount helper).
      - average_transaction_amount: total_transaction_value divided by the number
            of transactions with a valid amount.
    
    Note: It is assumed that the helper function `average_amount(amount_str)`
    is available in the scope.
    """
    c = conn.cursor()
    
    # Fetch all senator IDs from the senators table.
    c.execute("SELECT senator_id FROM senators")
    senator_ids = [row[0] for row in c.fetchall()]
    
    for senator_id in senator_ids:
        # Join transactions with filings on ptr_id to get transactions for the senator.
        c.execute("""
            SELECT t.type, t.asset_type, t.owner, t.amount
            FROM transactions t
            JOIN filings f ON t.ptr_id = f.ptr_id
            WHERE f.senator_id = ?
        """, (senator_id,))
        rows = c.fetchall()
        
        # If no transactions exist for this senator, skip updating.
        if not rows:
            continue
        
        # Initialize counters and accumulators.
        total_tx_count = 0
        purchase_count = 0
        exchange_count = 0
        sale_count = 0
        stock_tx_count = 0
        other_tx_count = 0
        
        ownership_child = 0
        ownership_dependent_child = 0
        ownership_joint = 0
        ownership_self = 0
        ownership_spouse = 0
        
        total_transaction_value = 0.0
        count_valid_amount = 0
        
        for row in rows:
            # Each row contains: (type, asset_type, owner, amount)
            tx_type, asset_type, owner, amount_str = row
            total_tx_count += 1
            
            # For purchase count, count transactions whose type is one of the given five values.
            if tx_type == 'Purchase':
                purchase_count += 1
                
            # Count exchange transactions.
            if tx_type == 'Exchange':
                exchange_count += 1
                
            # Count sale transactions (all sale types).
            if tx_type in ('Sale', 'Sale (Full)', 'Sale (Partial)'):
                sale_count += 1
                
            # Count stock vs. non-stock transactions.
            if asset_type == "Stock":
                stock_tx_count += 1
            else:
                other_tx_count += 1
                
            # Count ownership types.
            if owner == "Child":
                ownership_child += 1
            if owner == "Dependent Child":
                ownership_dependent_child += 1
            if owner == "Joint":
                ownership_joint += 1
            if owner == "Self":
                ownership_self += 1
            if owner == "Spouse":
                ownership_spouse += 1
                
            # Process the transaction amount using the helper function.
            # It converts a range (e.g. "$50,001-$100,000") into an average value (e.g. 75000).
            value = average_amount(amount_str)
            if value is not None:
                total_transaction_value += value
                count_valid_amount += 1
        
        average_transaction_amount = (total_transaction_value / count_valid_amount
                                      if count_valid_amount else 0)
        
        # Update the analytics table for the left side fields.
        c.execute("""
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
                average_transaction_amount = excluded.average_transaction_amount
        """, (
            senator_id,
            total_tx_count,
            purchase_count,
            exchange_count,
            sale_count,
            stock_tx_count,
            other_tx_count,
            ownership_child,
            ownership_dependent_child,
            ownership_joint,
            ownership_self,
            ownership_spouse,
            total_transaction_value,
            average_transaction_amount
        ))
    conn.commit()
    print("Senators analytics left fields updated successfully.")

def update_senators_analytics(conn):
    """
    Updates the analytics table for all senators by calling the two functions
    update_senators_analytics_left and update_senators_analytics_right.
    """
    # Initialize the analytics table.
    init_analytics_table(conn)

    # Function that operates on transactions_analytics table.
    update_senators_analytics_right(conn)

    time.sleep(1)

    # Function that operates on transactions and filings tables.
    update_senators_analytics_left(conn)