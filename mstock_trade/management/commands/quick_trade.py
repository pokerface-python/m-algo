from django.core.management.base import BaseCommand
import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("MSTOCK_API_KEY")
ACCESS_TOKEN = os.getenv("MSTOCK_ACCESS_TOKEN")
HEADERS = {
    "X-Mirae-Version": "1",
    "Authorization": f"token {API_KEY}:{ACCESS_TOKEN}",
    "Content-Type": "application/x-www-form-urlencoded"
}

ORDER_URL = "https://api.mstock.trade/openapi/typea/orders/regular"

class Command(BaseCommand):
    help = "Place a quick buy order and a target sell order"

    def handle(self, *args, **kwargs):
        symbol = "SENSEX2552081900CE"
        exchange = "BFO"
        qty = "20"
        buy_price = "55.2"
        sell_price = "57.4"
        product = "NRML"
        order_type = "SL" # SL FOR HIGHER PRICE BUY , ALSO INCLUDE TRIGGER PRICE
        validity = "DAY"

        buy_payload = {
            "tradingsymbol": symbol,
            "exchange": exchange,
            "transaction_type": "BUY",
            "order_type": order_type,
            "quantity": qty,
            "price": buy_price,
            "product": product,
            "validity": validity,
            "trigger_price": 55
        }

        self.stdout.write("Placing BUY order...")
        buy_resp = requests.post(ORDER_URL, headers=HEADERS, data=buy_payload).json()

        order_id = None
        if isinstance(buy_resp, dict):
            if buy_resp.get("status") == "success":
                order_id = buy_resp["data"]["order_id"]
                self.stdout.write(f"✅ BUY order placed: {order_id}")
            else:
                self.stdout.write(f"❌ BUY failed: {buy_resp.get('message')}")
                # time.sleep(1)  # Wait a moment
        elif isinstance(buy_resp, list):
            for item in buy_resp:
                if item.get("status") == "success":
                        order_id = item["data"]["order_id"]
                        self.stdout.write(f"✅ BUY order placed: {order_id}")
                else:
                    self.stdout.write(f"❌ BUY failed: {item.get('message')}")
            # breakpoint()
            # for error in buy_resp:
            #     self.stdout.write(f"❌ BUY failed: {error.get('message')}")
            if order_id:
                time.sleep(1)
                sell_payload = {
                    "tradingsymbol": symbol,
                    "exchange": exchange,
                    "transaction_type": "SELL",
                    "order_type": "LIMIT",
                    "quantity": qty,
                    "price": sell_price,
                    "product": product,
                    "validity": validity
                }

                self.stdout.write("Placing SELL target order...")
                sell_resp = requests.post(ORDER_URL, headers=HEADERS, data=sell_payload).json()

                if isinstance(sell_resp, dict):
                    if sell_resp.get("status") == "success":
                        self.stdout.write(f"✅ SELL order placed: {sell_resp['data']['order_id']}")
                    else:
                        self.stdout.write(f"❌ SELL failed: {sell_resp.get('message')}")
                elif isinstance(sell_resp, list):
                    for item in sell_resp:
                        if item.get("status") == "success":
                            self.stdout.write(f"✅ SELL order placed: {item['data']['order_id']}")
                        else:
                            self.stdout.write(f"❌ SELL failed: {item.get('message')}")
                else:
                    self.stdout.write(f"❌ Unexpected SELL response format: {sell_resp}")

        #     if sell_resp.get("status") == "success":
        #         self.stdout.write(f"✅ SELL order placed: {sell_resp['data']['order_id']}")
        #     else:
        #         self.stdout.write(f"❌ SELL failed: {sell_resp.get('message')}")
        # else:
        #     self.stdout.write(f"❌ BUY failed: {buy_resp.get('message')}")
