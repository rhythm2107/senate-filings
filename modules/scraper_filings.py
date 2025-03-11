import requests
import sqlite3
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import datetime
import logging
from modules.config import USE_DATE_FILTER, DATE_FILTER_DAYS, DB_NAME
from modules.session_utilis import get_csrf_token
from modules.db_helper import (
    init_db, init_filing_scrape_log, insert_filing, insert_filing_scrape_log,
    init_senators_tables, get_senator_id_by_alias  # <-- NEW import
)

# Get the main_logger object
logger = logging.getLogger("main_logger")

if USE_DATE_FILTER:
    submitted_start_date = (datetime.datetime.now() - datetime.timedelta(days=DATE_FILTER_DAYS)).strftime("%m/%d/%Y") + " 00:00:00"
else:
    # When not filtering, you could use an earlier date or an empty string.
    submitted_start_date = '01/01/2012 00:00:00'

# Extract the PTR (or paper) id using a regex pattern for a GUID.
def extract_ptr_id(link_html):
    match = re.search(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', link_html)
    return match.group(1) if match else None

def fetch_page(session, headers, payload, start, expected_length, url):
    payload['start'] = str(start)
    retries = 0
    while retries < 3:
        response = session.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            page_data = response_json.get('data', [])
            total_records = int(response_json.get('recordsTotal', 0))
            logger.debug(f"[DEBUG] Page start: {start}, Expected rows: {expected_length}, Received rows: {len(page_data)}")
            if page_data:
                logger.debug(f"[DEBUG] First row: {page_data[0]}")
                logger.debug(f"[DEBUG] Last row: {page_data[-1]}")
            # If not the last page and we received fewer rows than expected, retry.
            if len(page_data) < expected_length and (start + expected_length) < total_records:
                logger.debug(f"[DEBUG] Incomplete data at start {start}. Retrying (attempt {retries + 1})...")
                retries += 1
                time.sleep(2)
            else:
                return page_data
        else:
            logger.debug(f"[DEBUG] HTTP error {response.status_code} at start {start}; retrying (attempt {retries + 1})...")
            retries += 1
            time.sleep(2)
    logger.debug(f"[DEBUG] Failed to fetch complete data for page starting at {start} after 3 attempts.")
    return []

def fetch_filings(session, headers, payload_base, expected_length=100):
    url = "https://efdsearch.senate.gov/search/report/data/"
    # Get initial data to determine the total record count.
    payload = payload_base.copy()
    payload['start'] = '0'
    response = session.post(url, data=payload, headers=headers)
    if response.status_code != 200:
        logger.debug(f"[DEBUG] Failed to retrieve initial data, status: {response.status_code}")
        return []
    data = response.json()
    total_records = int(data.get('recordsTotal', 0))
    logger.debug(f"[DEBUG] Total records according to first response: {total_records}")
    filings = []

    # Loop through pages based on the captured total record count.
    for start in range(0, total_records, expected_length):
        logger.debug(f"[DEBUG] Fetching records starting at {start}...")
        page_data = fetch_page(session, headers, payload, start, expected_length, url)
        filings.extend(page_data)
        logger.debug(f"[DEBUG] Total filings collected so far: {len(filings)}")
        time.sleep(2)  # delay to avoid rate limits

    return filings

def scrape_filings():
    # Set up the session and headers
    session = requests.Session()
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9,pl;q=0.8',
        'Connection': 'keep-alive',
        'Content-Length': '1385',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'efdsearch.senate.gov',
        'Origin': 'https://efdsearch.senate.gov',
        'Referer': 'https://efdsearch.senate.gov/search/',
        'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'X-Csrftoken': '3tHsilnrXTwoGWAgauMFS34eKfCqJzq6jHihXeXaLBDywoXG0xo82qjMnyKPqmce',
        'X-Requested-With': 'XMLHttpRequest'
    }
    headers = get_csrf_token(session, headers)
    
    # Define the base payload (do not change the key authentication/payload parts)
    # IMPORTANT: The 'order[0][column]' is set to '4' to force sorting by filing date.
    # This value must remain '4' in future revisions to maintain a consistent sort order and successful scraping.
    payload_base = {
        'draw': '1',
        'columns[0][data]': '0',
        'columns[0][name]': '',
        'columns[0][searchable]': 'true',
        'columns[0][orderable]': 'true',
        'columns[0][search][value]': '',
        'columns[0][search][regex]': 'false',
        'columns[1][data]': '1',
        'columns[1][name]': '',
        'columns[1][searchable]': 'true',
        'columns[1][orderable]': 'true',
        'columns[1][search][value]': '',
        'columns[1][search][regex]': 'false',
        'columns[2][data]': '2',
        'columns[2][name]': '',
        'columns[2][searchable]': 'true',
        'columns[2][orderable]': 'true',
        'columns[2][search][value]': '',
        'columns[2][search][regex]': 'false',
        'columns[3][data]': '3',
        'columns[3][name]': '',
        'columns[3][searchable]': 'true',
        'columns[3][orderable]': 'true',
        'columns[3][search][value]': '',
        'columns[3][search][regex]': 'false',
        'columns[4][data]': '1',
        'columns[4][name]': '',
        'columns[4][searchable]': 'true',
        'columns[4][orderable]': 'true',
        'columns[4][search][value]': '',
        'columns[4][search][regex]': 'false',
        'order[0][column]': '4',   # DO NOT CHANGE THIS VALUE. Must remain '4' to ensure correct sorting.
        'order[0][dir]': 'desc',
        'start': '0',
        'length': '100',
        'search[value]': '',
        'search[regex]': 'false',
        'report_types': '[11]',
        'filer_types': '[]',
        'submitted_start_date': submitted_start_date, # Scraper will only look at filings from seven days ago
        'submitted_end_date': '',
        'candidate_state': '',
        'senator_state': '',
        'office_id': '',
        'first_name': '',
        'last_name': ''
    }
    
    logger.info("Starting data fetch...")
    filings_data = fetch_filings(session, headers, payload_base)
    logger.info(f"Fetched a total of {len(filings_data)} filings.")

    # Initialize database, filings table, and the filing scrape log table.
    conn = init_db()
    init_filing_scrape_log(conn)
    init_senators_tables(conn)
    
    # Insert filings and log the scrape event.
    for item in filings_data:
        # Each item is expected to be in the form:
        # [first_name, last_name, filing_info, link_html, filing_date]
        first_name = item[0].upper().strip() # Ensuring consistency of case & strip trailing spaces
        last_name = item[1].upper().strip() # Ensuring consistency of case & strip trailing spaces
        filing_info = item[2]
        link_html = item[3]
        filing_date = item[4]
        
        ptr_id = extract_ptr_id(link_html)
        
        # Also extract the URL from the HTML
        link_match = re.search(r'href="([^"]+)"', link_html)
        filing_url = link_match.group(1) if link_match else ""
        
        # Determine filing type based on the URL.
        # If the URL contains "ptr", it's an online filing; if it contains "paper", it's a paper filing.
        if "ptr" in filing_url.lower():
            filing_type = "Online"
        elif "paper" in filing_url.lower():
            filing_type = "Paper"
        else:
            filing_type = "Unknown"


        full_name = f"{first_name} {last_name}"
        alias_name = full_name
        senator_id = get_senator_id_by_alias(conn, alias_name)

        if senator_id is None:
            # We haven't recognized this name yet. We'll log and continue.
            logger.info(f"Unknown senator name: {alias_name} for ptr_id={ptr_id}. Manual review needed.")
        else:
            logger.debug(f"Resolved alias '{alias_name}' to senator_id {senator_id}")
        
        filing_tuple = (ptr_id, first_name, last_name, full_name, filing_info, filing_url, filing_date, filing_type)
        insert_filing(conn, filing_tuple)
        # Log the scraping event for this filing.
        insert_filing_scrape_log(conn, ptr_id)
        
        logger.debug(f"Inserted filing {ptr_id} for {first_name} {last_name} with type {filing_type} and logged scrape time.")
    
    conn.close()
    logger.info("Data insertion complete.")