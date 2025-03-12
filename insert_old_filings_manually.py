import pandas as pd
from modules.db_helper import init_db, init_transactions_table, insert_transaction

def extract_clipboard_to_tuple_list():
    # Read data directly from clipboard (assuming tab-separated data from Google Sheets)
    df = pd.read_clipboard(sep='\t', header=None)

    # Convert DataFrame rows into a list of tuples
    data_tuples = [tuple(row) for row in df.itertuples(index=False, name=None)]
    return data_tuples

def extract_all_tx_from_clipboard():
    tx_tuples = []

    data_tuples = extract_clipboard_to_tuple_list()
    for item in data_tuples:
        print("ITEM_1", item)
        ptr_id             = item[0]
        first_name         = item[1]
        last_name          = item[2]
        filing_date        = item[3]
        transaction_number = item[4]
        transaction_date   = item[5]
        owner              = item[6]
        ticker             = item[7]
        asset_name         = item[8]
        additional_info    = ''
        asset_type         = item[9]
        txn_type           = item[10]
        amount             = item[11]
        comment            = ''

        try:
            txn_num_int = int(transaction_number)
        except ValueError:
            txn_num_int = None

        transaction_tuple = (
            ptr_id,
            txn_num_int,
            transaction_date,
            owner,
            ticker,
            asset_name,
            additional_info,
            asset_type,
            txn_type,
            amount,
            comment
        )

        print("ITEM_2", transaction_tuple)

        tx_tuples.append(transaction_tuple)

    return tx_tuples

if __name__ == '__main__':
    # Establish a connection and ensure tables are created
    conn = init_db()
    init_transactions_table(conn)
    tx_tuples = extract_all_tx_from_clipboard()

    total_inserted_tx = 0

    for tuple in tx_tuples:
        print(f"Processing transaction {tuple}")
        insert_transaction(conn, tuple)
        total_inserted_tx += 1

    print(f"Total transactions inserted: {total_inserted_tx}")