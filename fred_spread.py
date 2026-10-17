from dotenv import load_dotenv
import os
import requests
import sys

load_dotenv()

if (os.getenv("FRED_KEY")):
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
    response = requests.get('https://api.stlouisfed.org/fred/series/observations', params=fred_params, timeout=5)

    if response.status_code != 200:
        output = f'Error {response.status_code}. Try again.'
        print(output, file=sys.stderr)
        sys.exit(1)
    else:
        data = response.json()
        if data["observations"]:
            for obs in data["observations"]:
                if obs["value"] == ".":
                    continue
                else:
                    output = f'10Y-2Y spread: {float(obs["value"]):.2f}% ({obs["date"]})'
                    print(output)
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
