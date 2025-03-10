from bs4 import BeautifulSoup

def get_csrf_token(session, headers):
    """
    Gets the CSRF token from a basic request and updates the headers.
    """
    url = 'https://efdsearch.senate.gov/search/'
    response = session.get(url)
    if 'csrftoken' in response.cookies:
        headers['X-Csrftoken'] = response.cookies['csrftoken']
    return headers

def accept_disclaimer(session, proxy=None):
    """
    Accepts the disclaimer on the home page and returns necessary tokens.
    """
    initial_url = 'https://efdsearch.senate.gov/search/home/'
    initial_response = session.get(initial_url, proxies=proxy)
    
    # Get tokens from cookies
    if 'csrftoken' in initial_response.cookies:
        csrftoken = initial_response.cookies['csrftoken']
        number_token = initial_response.cookies.get('33a5c6d97f299a223cb6fc3925909ef7', '')
    else:
        csrftoken = ''
        number_token = ''
    
    # Extract CSRF middleware token from the HTML
    soup = BeautifulSoup(initial_response.text, 'html.parser')
    csrf_input = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})
    csrf_middlewaretoken = csrf_input['value'] if csrf_input else ''
    
    # Prepare headers for the disclaimer POST request
    disclaimer_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '108',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': f'csrftoken={csrftoken}; 33a5c6d97f299a223cb6fc3925909ef7={number_token}',
        'Host': 'efdsearch.senate.gov',
        'Origin': 'https://efdsearch.senate.gov',
        'Referer': 'https://efdsearch.senate.gov/search/home/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    disclaimer_payload = {
        'prohibition_agreement': 1,
        'csrfmiddlewaretoken': csrf_middlewaretoken,
    }
    
    disclaimer_post_response = session.post(initial_url, data=disclaimer_payload, headers=disclaimer_headers, 
                                              allow_redirects=False, proxies=proxy)
    
    if disclaimer_post_response.status_code == 302:
        print("Disclaimer accepted. Session established successfully.")
        # Try to extract a session id from the response headers if available.
        if 'Set-Cookie' in disclaimer_post_response.headers:
            set_cookie_header = disclaimer_post_response.headers['Set-Cookie']
            # Adjust parsing based on how the cookie is formatted.
            session_id = set_cookie_header.split(';')[0].replace('sessionid=', '')
        else:
            session_id = ''
        return csrftoken, session_id, number_token
    else:
        print("Failed to accept disclaimer. Status code:", disclaimer_post_response.status_code)
        return csrftoken, '', number_token