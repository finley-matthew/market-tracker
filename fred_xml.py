import os
import sys
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv

load_dotenv()

if os.getenv("FRED_KEY"):
    print("FRED_KEY is set.", file=sys.stderr)
else:
    print("FRED_KEY is not set.", file=sys.stderr)
    sys.exit(1)

try:
    fred_params = {"api_key": os.getenv("FRED_KEY"),
                   "series_id": "T10Y2Y",
                   "file_type": "xml",
                   "limit": 3,
                   "sort_order": "desc"}
    response = requests.get("https://api.stlouisfed.org/fred/series/observations",
                            params=fred_params,
                            timeout=5)

    if response.status_code != 200:
        print(f"Error {response.status_code}. Try again.", file=sys.stderr)
        sys.exit(1)
    else:
        root = ET.fromstring(response.text)
        for child in root:
            value = child.get("value")
            date = child.get("date")
            if value == ".":
                continue
            else:
                print(f"10Y-2Y spread: {float(value):.2f}% ({date})")
                break

except requests.exceptions.Timeout as e:
    print(f"Connection Timeout. {type(e).__name__}", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error. {type(e).__name__}", file=sys.stderr)
    sys.exit(1)
except ET.ParseError as e:
    print(f"ElementTree ParseError. {e}", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"Exception Error. {type(e).__name__}", file=sys.stderr)
    sys.exit(1)
