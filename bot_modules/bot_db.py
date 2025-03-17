import sqlite3

def get_senators():
    conn = sqlite3.connect("filings.db")
    c = conn.cursor()
    c.execute("SELECT senator_id, canonical_full_name FROM senators ORDER BY senator_id")
    rows = c.fetchall()
    conn.close()
    return rows

