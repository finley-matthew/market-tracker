import os
import sys
from dotenv import load_dotenv
import requests

load_dotenv()

if os.getenv("FRED_KEY"):
    print("FRED_KEY is set.")
else:
    print("FRED_KEY is not set.")
    sys.exit(1)

try:
    fred_params = {"api_key": os.getenv("FRED_KEY"),
                   "series_id": "T10Y2Y",
                   "file_type": "json",
                   "limit": 10,
                   "sort_order": "desc"}
    response = requests.get("https://api.stlouisfed.org/fred/series/observations",
                            params=fred_params,
                            timeout=5)

    if response.status_code != 200:
        print(f"Error {response.status_code}. Try again.", file=sys.stderr)
        sys.exit(1)
    else:
        data = response.json()
        if data["observations"]:
            for obs in data["observations"]:
                value = obs["value"]
                date = obs["date"]
                if obs["value"] == ".":
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
except requests.exceptions.JSONDecodeError as e:
    print(f"JSON Decode Error. {type(e).__name__}", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"Exception Error. {type(e).__name__}", file=sys.stderr)
    sys.exit(1)
