# yourapp/ws_market_client.py
import asyncio
import websockets
import struct

# API_KEY = "YOUR_API_KEY"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVU0VSTkFNRSI6Ik1BMzUyMTE3NCIsIlVTRVJfREVUQUlMUyI6IklvbXdlb1YzUWNtYytXMFFkckNZN09PR1Myam5JNXV3dm0vV3hwdC9LbkFSS21WdXh1SVM1bCs4Y2NHdEsvblBCWTU4QW5LNmdwc2czNWZvZVVDeUNhMGo0dHRtYythTGFObVlSRGM2T3FkVUZxQ1VROU43c0RMT29jRGljcXg5ZXZlTEJaZHU3TmQzVUtUQXhraFUrbXR4R09Qc25ucEUxQ3NjdG1HUWJxNkNXRUVsZTROMDVsdWpxTjFjYjlVWkk5ZXRqcVVtRmdnV0JMWk9OeDdTWXV1L0luWHlFbEZJL211RFdhRDZsQUNxZnBVUlBFVlRjcDZMSGd5SUxwOEZvUnAwMC94d2dOVloxUkJRYzlHV1N3RTdLaktRUFN3V3FER0F1clljR1ZZaFBLNDVHbW9nQUlIMWppNWtoaFNtdTI3N3d1b3gvdmhrMkpDRXlydUxQMWRvVTh6RTYvUW41UElGMzQyeWQwNU5TUHp5ano2cjhUOTNtZHk1U0kvWSIsIlVTRVJJRCI6Ik1BMzUyMTE3NCIsIkFDQ0VTU19UT0tFTiI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUpoZFdRaU9pSnRhWEpoWlM1cGJpSXNJbVY0Y0NJNk1UYzBOemN5TmpNek1pd2lhV0YwSWpveE56UTNOak01T1RNeUxDSnBjM01pT2lKdGFYSmhaUzVwYmlJc0ltNWlaaUk2TVRRME5EUTNPRFF3TUN3aWNHWnRJam9pTVNJc0luUnBaQ0k2SWpreUlpd2lkV2xrSWpvaU1USTBNVGt4TmlJc0luWnBaQ0k2SWpJeEluMC5Kc2lBa3pNeUNSU00zcU5KME9SaEoxUndKTlJGaWN6Qkx0ajVsZXpUM0VRIiwiQVBJVFlQRSI6IlRZUEVBIiwiVUlEIjoiNDUxOTI5MDYtYjhiYi00OTJkLTk2MmMtNjI1NDlhMjE4MTQzIiwibmJmIjoxNzQ3NjM5OTMyLCJleHAiOjE3NDc2ODMxMzIsImlhdCI6MTc0NzYzOTkzMn0.PcEKkFJpns6vmNOOg8CED0stwkvKpP_y5BuJITypfFw"
API_KEY = "SiiuFL+tN4x5RoWxPXvTXoj34CAsAt32cZQn8R5Lfzo@"

WS_URL = f"wss://ws.mstock.trade?API_KEY={API_KEY}&ACCESS_TOKEN={ACCESS_TOKEN}"

# Helper to parse a single 64-byte quote packet
def parse_quote_packet(packet):
    data = struct.unpack('>16i', packet[:64])
    return {
        "token": data[0],
        "ltp": data[1] / 100.0,  # Prices are usually in paise
        "qty": data[2],
        "avg_price": data[3] / 100.0,
        "volume": data[4],
        "buy_qty": data[5],
        "sell_qty": data[6],
        "open": data[7] / 100.0,
        "high": data[8] / 100.0,
        "low": data[9] / 100.0,
        "close": data[10] / 100.0,
        "ts": data[11],
        "oi": data[12],
        "oi_high": data[13],
        "oi_low": data[14],
        "exch_ts": data[15]
    }
buffer = b""
async def market_data_listener():
    async with websockets.connect(WS_URL) as ws:
        # Send login message to keep connection alive
        await ws.send(f"LOGIN:{ACCESS_TOKEN}")
        print("Sent LOGIN")

        # Subscribe to instruments (e.g., 55256, 55412)
        await ws.send('{"a": "subscribe", "v": [55256, 55412]}')
        await ws.send('{"a": "mode", "v": ["ltp"]}')
        print("Subscribed to tokens")

        # while True:
        #     msg = await ws.recv()
        #     if isinstance(msg, bytes):
        #         num_packets = struct.unpack(">H", msg[:2])[0]
        #         total_bytes = struct.unpack(">H", msg[2:4])[0]

        #         print(f"Packets: {num_packets}, Total Bytes: {total_bytes}")
        #         for i in range(num_packets):
        #             start = 4 + i * 64
        #             end = start + 64
        #             quote = parse_quote_packet(msg[start:end])
        #             print("Quote:", quote)
        #     else:
        #         print("Received non-binary message:", msg)
        while True:
            msg = await ws.recv()
            if isinstance(msg, bytes):
                buffer += msg  # Accumulate bytes
                while len(buffer) >= 64:  # Check if we have at least one full packet
                    packet = buffer[:64]
                    buffer = buffer[64:]  # Remove processed bytes
                    quote = parse_quote_packet(packet)
                    if quote:
                        print("Quote:", quote)
            else:
                print("Received non-binary message:", msg)
# Run the listener
if __name__ == "__main__":
    asyncio.run(market_data_listener())
