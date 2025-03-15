import re
import logging

logger = logging.getLogger("main_logger")

def format_amount(part):
    """
    Takes a part of an amount string (e.g. "$15 001" or "Over $50,000,000") and returns it in a standardized format,
    e.g. "$15,001" or "Over $50,000,000".
    """
    part = part.strip()
    over_flag = False
    if part.upper().startswith("OVER"):
        over_flag = True
        part = part[len("OVER"):].strip()
    
    dollar_flag = False
    if part.startswith("$"):
        dollar_flag = True
        part = part[1:].strip()
    
    # Remove all spaces and commas to get the raw number
    raw_number = re.sub(r"[ ,]", "", part)
    try:
        number = int(raw_number)
    except ValueError:
        return part  # if conversion fails, return the original part
    
    # Format the number with commas as thousands separators
    formatted_number = format(number, ",")
    result = ""
    if dollar_flag:
        result += "$"
    result += formatted_number
    if over_flag:
        result = "Over " + result
    return result

def normalize_amount_field_format(amount_str):
    """
    Normalizes an amount range string.
    Example outputs:
      "$1 000 001-$5 000 000" becomes "$1,000,001-$5,000,000"
      "$15,001 - $50,000" becomes "$15,001-$50,000"
    """
    # Remove extra spaces around the hyphen and split on hyphen
    parts = re.split(r'\s*-\s*', amount_str)
    if len(parts) == 1:
        # Single value, just format it.
        return format_amount(parts[0])
    elif len(parts) == 2:
        return f"{format_amount(parts[0])}-{format_amount(parts[1])}"
    else:
        # Unexpected format; return as-is
        return amount_str
    
import re

def average_amount(amount_str):
    """
    Given an amount range string in one of the expected formats, return the average value as an integer.
    Examples:
      "$1,000,001-$5,000,000" returns (1000001 + 5000000) // 2
      "$15,001-$50,000" returns (15001 + 50000) // 2
      "Over $50,000,000" returns the numeric value after "Over" (or you could decide a different logic).
    """
    s = amount_str.strip()
    # Handle "Over" case: we'll just remove "Over" and return the numeric part
    if s.lower().startswith("over"):
        # Remove the "Over" text, then remove $ and commas
        s = s[4:].strip()
        if s.startswith("$"):
            s = s[1:].strip()
        s = s.replace(",", "")
        try:
            return int(s)
        except ValueError:
            return None
    # Assume it's a range separated by a dash
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 2:
            low_str = parts[0].replace("$", "").replace(",", "").strip()
            high_str = parts[1].replace("$", "").replace(",", "").strip()
            try:
                low = int(low_str)
                high = int(high_str)
                return (low + high) // 2
            except ValueError:
                return None
    # Otherwise, attempt to parse a single numeric value
    s = s.replace("$", "").replace(",", "").strip()
    try:
        return int(s)
    except ValueError:
        return None
    
import os

def get_ignore_tickers(file_path="resources/ignore_tickers.txt"):
    """
    Read and return a list of tickers to ignore from the specified file located
    in the resources folder of your module. Each ticker should be on a separate line.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, file_path)
    try:
        with open(full_path, "r") as f:
            ignore_tickers = [line.strip().lstrip('$') for line in f if line.strip()]
        return ignore_tickers
    except FileNotFoundError:
        logger.warning(f"Ignore file not found: {full_path}. No tickers will be ignored.")
        return []
