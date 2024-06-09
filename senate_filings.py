import requests

url = "https://efdsearch.senate.gov/search/report/data/"

payload = {
    'draw': '2',
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
    'columns[4][data]': '4',
    'columns[4][name]': '',
    'columns[4][searchable]': 'true',
    'columns[4][orderable]': 'true',
    'columns[4][search][value]': '',
    'columns[4][search][regex]': 'false',
    'order[0][column]': '4',
    'order[0][dir]': 'desc',
    'start': '1600',
    'length': '1700',
    'search[value]': '',
    'search[regex]': 'false',
    'report_types': '[11]',
    'filer_types': '[1]',
    'submitted_start_date': '01/01/2012 00:00:00',
    'submitted_end_date': '',
    'candidate_state': '',
    'senator_state': '',
    'office_id': '',
    'first_name': '',
    'last_name': ''
}

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

# Using a session to manage cookies and CSRF token
session = requests.Session()

# Get the CSRF token from the initial request
initial_response = session.get('https://efdsearch.senate.gov/search/')
if 'csrftoken' in initial_response.cookies:
    csrftoken = initial_response.cookies['csrftoken']
    headers['X-Csrftoken'] = csrftoken

# Making the POST request with the session
response = session.post(url, data=payload, headers=headers)

item_count = 0

if response.status_code == 200:
    data = response.json()
    
    for item in data['data']:
        print('ITEM', item)
        item_count += 1
        with open('efdsearch_senate_filings.txt', 'a') as file:
          file.write(f"{str(item)}\n")

else:
    print(f"Failed to retrieve data: {response.status_code}")
    print(response.text)
