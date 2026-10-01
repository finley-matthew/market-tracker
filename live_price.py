#Live market data from API
import requests

try:
    response = requests.get('https://api.gold-api.com/price/XAU', timeout=5)

    if response.status_code != 200:
        output = f'Error {response.status_code}. Please try again.'
        print(output)

    else:
        data = response.json()
        price = data["price"]
        output =  f'{data["name"]} ({data["symbol"]}): {data["currencySymbol"]}{price:.2f} {data["currency"]}'
        print(output)
except requests.exceptions.Timeout:
    print("Connection Timeout. Try again.")
except requests.exceptions.ConnectionError:
    print("Connection Error. Try again.")