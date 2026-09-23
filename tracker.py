import json

with open("sample_price.json", "r") as file:
    data = json.load(file)

for key in data:
    new_price = data[key]["price"]
    output = f'{data[key]["name"]} ({data[key]["symbol"]}): {new_price:.2f} {data[key]["currency"]} as of {data[key]["timestamp"]}'
    print(output)