# your_app/management/commands/auto_trade.py

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
VIEW_ALL_ORDERS_URL = "https://api.mstock.trade/openapi/typea/orders"
CANCEL_ALL_ORDERS_URL = "https://api.mstock.trade/openapi/typea/orders/cancelall"

class Command(BaseCommand):
    help = "Place a quick buy order and a target sell order after it is traded"

    def handle(self, *args, **kwargs):
        # symbol = "SENSEX2552081200PE"
        symbol = "SENSEX25MAY78500PE"
        exchange = "BFO"
        qty = "20"
        buy_price = "52"
        sell_price = "53.4"
        product = "NRML"
        order_type = "SL"  # SL for stop-loss entry
        validity = "DAY"
        trigger_price = "51.8"

        # Step 1: Place BUY order
        buy_payload = {
            "tradingsymbol": symbol,
            "exchange": exchange,
            "transaction_type": "BUY",
            "order_type": order_type,
            "quantity": qty,
            "price": buy_price,
            "product": product,
            "validity": validity,
            "trigger_price": trigger_price
        }

        self.stdout.write("📈 Placing BUY order...")
        buy_resp = requests.post(ORDER_URL, headers=HEADERS, data=buy_payload).json()

        # if not isinstance(buy_resp, dict) or buy_resp.get("status") != "success":
        #     self.stdout.write(f"❌ BUY order failed: {buy_resp}")
        #     return
        print('status --- ', buy_resp)

        order_id = None
        sell_order_id = None
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

        if not order_id:
            self.stdout.write("❌ No valid BUY order_id found. Exiting.")
            return

        # self.stdout.write(f"✅ BUY order placed: {order_id}")

        # Step 2: Poll /orders to check for Traded status
        self.stdout.write("⏳ Waiting for BUY order to be traded...")
        # max_retries = 160
        # retry_delay = 1  # seconds

        # for i in range(max_retries):
        #     orders_resp = requests.get(VIEW_ALL_ORDERS_URL, headers=HEADERS).json()
        #     if orders_resp.get("status") == "success":
        #         orders = orders_resp.get("data", [])
        #         # breakpoint()
        #         for order in orders:
                    
        #             # if order.get("order_id") == order_id:
        #             if str(order.get("order_id")) == str(order_id):
        #                 status = order.get("status")
        #                 self.stdout.write(f"🔍 Check {i + 1}: Order status = {status}")
        #                 if status == "Traded":
        #                     self.stdout.write("✅ BUY order traded successfully.")
        #                     break
        #         else:
        #             time.sleep(retry_delay)
        #             continue
        #         break
        #     else:
        #         self.stdout.write(f"⚠️ Failed to fetch orders: {orders_resp}")
        #         time.sleep(retry_delay)
        # else:
        #     self.stdout.write("❌ BUY order did not get traded within expected time.")
        #     return

        for attempt in range(60):
            resp = requests.get(VIEW_ALL_ORDERS_URL, headers=HEADERS).json()
            if resp.get("status") == "success":
                latest_order = resp["data"][0] if resp["data"] else None
                if latest_order and latest_order["order_id"] == order_id:
                    status = latest_order["status"]
                    self.stdout.write(f"🔍 Attempt {attempt+1}: Latest order status = {status}")
                    
                    if status == "Traded":
                        self.stdout.write("✅ BUY order is now TRADED.")
                        break
                    if status == "Cancelled":
                        self.stdout.write("❌ BUY order was CANCELLED. Exiting.")
                        return
                    if status == "Rejected":
                        self.stdout.write("❌ BUY order was REJECTED. Exiting.")
                        return
                else:
                    self.stdout.write("⏳ Waiting for latest order to update...")
            else:
                self.stdout.write(f"⚠️ Error fetching order status: {resp}")
            time.sleep(2)
        else:
            self.stdout.write("❌ BUY order was not traded in time.")


        # Step 4: Cancel all orders
            self.stdout.write("🛑 Cancelling all pending orders...")
            cancel_resp = requests.post(CANCEL_ALL_ORDERS_URL, headers=HEADERS).json()
            if cancel_resp.get("status") == "success":
                self.stdout.write("✅ All orders cancelled successfully.")
            else:
                self.stdout.write(f"❌ Failed to cancel orders: {cancel_resp}")
            return
            return
        # Step 3: Place SELL order
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

        self.stdout.write("📉 Placing SELL order...")
        sell_resp = requests.post(ORDER_URL, headers=HEADERS, data=sell_payload).json()
        if isinstance(sell_resp, dict):
            if sell_resp.get("status") == "success":
                sell_order_id = sell_resp['data']['order_id']
                self.stdout.write(f"✅ SELL order placed: {sell_resp['data']['order_id']}")
            else:
                self.stdout.write(f"❌ SELL order failed: {sell_resp}")
        elif isinstance(sell_resp, list):
            for item in sell_resp:
                if item.get("status") == "success":
                    self.stdout.write(f"✅ SELL order placed: {item['data']['order_id']}")
                else:
                    self.stdout.write(f"❌ SELL order failed: {item}")
        else:
            self.stdout.write(f"❌ Unexpected SELL response: {sell_resp}")

        # if isinstance(sell_resp, dict) and sell_resp.get("status") == "success":
        #     self.stdout.write(f"✅ SELL order placed: {sell_resp['data']['order_id']}")
        # else:
        #     self.stdout.write(f"❌ SELL order failed: {sell_resp}")


        if not sell_order_id:
            self.stdout.write("❌ No SELL order ID found. Exiting.")
            return
                
        self.stdout.write("⏳ Monitoring SELL order status...")
        for attempt in range(60):
            resp = requests.get(VIEW_ALL_ORDERS_URL, headers=HEADERS).json()
            if resp.get("status") == "success":
                latest_order = resp["data"][0] if resp["data"] else None
                if latest_order and latest_order["order_id"] == sell_order_id:
                    status = latest_order["status"]
                    self.stdout.write(f"🔍 Attempt {attempt+1}: Latest SELL order status = {status}")

                    if status == "Traded":
                        self.stdout.write("✅ SELL order is now TRADED.")
                        break
                    if status == "Cancelled":
                        self.stdout.write("❌ SELL order was CANCELLED. Exiting.")
                        return
                    if status == "Rejected":
                        self.stdout.write("❌ SELL order was REJECTED. Exiting.")
                        return
                else:
                    self.stdout.write("⏳ Waiting for latest SELL order to update...")
            else:
                self.stdout.write(f"⚠️ Error fetching SELL order status: {resp}")
            time.sleep(2)
        else:
            self.stdout.write("❌ SELL order was not traded in time.")