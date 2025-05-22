from django.core.management.base import BaseCommand
import os
import asyncio
import json
import struct
import websockets
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Starts the mStock feed and broadcasts to Channels group"

    def handle(self, *args, **options):
        load_dotenv()
        access_token = os.getenv('MSTOCK_ACCESS_TOKEN')
        api_key = os.getenv('MSTOCK_API_KEY')

        if not access_token or not api_key:
            print("Missing MSTOCK_ACCESS_TOKEN or MSTOCK_API_KEY in .env file.")
            return

        async def mstock_feed():
            channel_layer = get_channel_layer()
            uri = f"wss://ws.mstock.trade?API_KEY={api_key}&ACCESS_TOKEN={access_token}"
            async with websockets.connect(uri) as ws:
                await ws.send(f"LOGIN:{access_token}")
                await ws.send(json.dumps({"a": "subscribe", "v": [26000]}))
                await ws.send(json.dumps({"a": "mode", "v": ["ltp"]}))

                while True:
                    message = await ws.recv()
                    if isinstance(message, bytes):
                        num_packets = struct.unpack('>H', message[0:2])[0]
                        offset = 4
                        for _ in range(num_packets):
                            packet = message[offset:offset+32]
                            offset += 32
                            (token, ltp, high, low, open_price, close, change, timestamp) = struct.unpack('>iiiiiiii', packet)
                            data = {
                                'ltp': ltp / 100,
                                'high': high / 100,
                                'low': low / 100,
                                'open': open_price / 100,
                                'close': close / 100,
                                'change': change / 100,
                                'timestamp': timestamp
                            }
                            async_to_sync(channel_layer.group_send)(
                                "sensex",
                                {
                                    "type": "sensex_update",  # match your consumer
                                    "data": data
                                }
                            )
        asyncio.run(mstock_feed())
