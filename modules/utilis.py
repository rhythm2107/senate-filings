import re

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