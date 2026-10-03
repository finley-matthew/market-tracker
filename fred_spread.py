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
    response = requests.get('https://api.stlouisfed.org/fred/series/observations', params={"api_key": os.getenv("FRED_KEY"), "series_id": "T10Y2Y", "file_type": "json", "limit": 10, "sort_order": "desc"}, timeout = 5)

    if response.status_code != 200:
        output = f'Error {response.status_code}. Try again.'
        print(output)
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

except requests.exceptions.Timeout:
    print("Connection Timeout. Try again.")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print("Connection Error. Try again.")
    sys.exit(1)
except requests.exceptions.JSONDecodeError:
    print("JSON Decode Error. Try again.")
    sys.exit(1)
except requests.exceptions.RequestException:
    print("Exception Error. Try again.")
    sys.exit(1)