import requests

response = requests.get('https://api.gold-api.com/price/XAU')
data = response.json()

price = data["price"]
output =  f'{data["name"]} ({data["symbol"]}): {data["currencySymbol"]}{price:.2f} {data["currency"]}'

print(output)