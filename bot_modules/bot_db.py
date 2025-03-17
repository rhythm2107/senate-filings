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
