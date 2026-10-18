import json

with open("sample_price.json", "r") as file:
    data = json.load(file)

for key in data:
    name = data[key]["name"]
    symbol = data[key]["symbol"]
    price = data[key]["price"]
    currency = data[key]["currency"]
    timestamp = data[key]["timestamp"]
    print(f"{name} ({symbol}): {price:.2f} {currency} as of {timestamp}")
