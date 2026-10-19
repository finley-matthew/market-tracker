import logging

import requests

logger = logging.getLogger(__name__)

logging.basicConfig(filename="tracker.log",
                    format="%(asctime)s %(levelname)s %(message)s",
                    level=logging.INFO)

symbol = "XAU"

try:
    response = requests.get(f"https://api.gold-api.com/price/{symbol}", timeout=5)

    if response.status_code // 100 == 4:
        logger.error(f"ClientError {symbol} {response.status_code}")
    elif response.status_code // 100 == 5:
        logger.error(f"ServerError {symbol} {response.status_code}")
    else:
        data = response.json()
        name = data["name"]
        api_symbol = data["symbol"]
        currency_symbol = data["currencySymbol"]
        price = data["price"]
        currency = data["currency"]
        print(f"{name} ({api_symbol}): {currency_symbol}{price:.2f} {currency}")
        logger.info(f"{symbol} {price}")
except requests.exceptions.Timeout as e:
    logger.error(f"Timeout {symbol} {type(e).__name__}")
except requests.exceptions.ConnectionError as e:
    logger.error(f"ConnectionError {symbol} {type(e).__name__}")
except requests.exceptions.RequestException as e:
    logger.error(f"RequestException {symbol} {type(e).__name__}")
