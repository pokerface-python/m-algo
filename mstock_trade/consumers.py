
import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import websockets

import struct
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import traceback
import logging
from .models import Instrument
logger = logging.getLogger(__name__)

# token_list = [49212, 49210, 49244, 585
token_list = [500325, 49244,1175722,821476]
# token_list.extend(t)
instruments = Instrument.objects.filter(instrument_token__in=token_list)
TOKEN_SYMBOL_MAP = {
    int(inst.instrument_token): {
        "symbol": inst.trading_symbol,
        "exchange": inst.exchange,
        "lot_size": inst.lot_size
    }
    for inst in instruments
}

class StockConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Simple state tracking
        self.trade_status = "waiting_for_buy"  # waiting_for_buy -> buy_placed -> sell_placed -> completed
        self.buy_order_id = None
        self.sell_order_id = None
        
        # API configuration
        self.api_key = settings.MSTOCK_API_KEY
        self.access_token = settings.MSTOCK_ACCESS_TOKEN
        self.headers = {
            "X-Mirae-Version": "1",
            "Authorization": f"token {self.api_key}:{self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        self.order_url = "https://api.mstock.trade/openapi/typea/orders/regular"
        self.view_orders_url = "https://api.mstock.trade/openapi/typea/orders"
        self.cancel_all_orders_url = "https://api.mstock.trade/openapi/typea/orders/cancelall"

    
    async def connect(self):
        await self.accept()
        logger.info("WebSocket connection accepted")

        try:
            # Step 1: Prepare authentication details
            self.ws_url = f"wss://ws.mstock.trade?API_KEY={self.api_key}&ACCESS_TOKEN={self.access_token}"
            logger.info(f"Connecting to m.Stock at {self.ws_url}")

            # Step 2: Establish WebSocket connection to Mirae m.Stock
            self.websocket = await websockets.connect(self.ws_url)
            logger.info("Connected to m.Stock WebSocket")

            # Step 3: Send LOGIN message (mandatory within 10 seconds)
            login_msg = f"LOGIN:{self.access_token}"
            await self.websocket.send(login_msg)
            logger.info(f"Sent login message: {login_msg}")

            # Step 4: Subscribe to tokens (replace with your actual instrument tokens)
            # For testing, using a known valid token - modify as needed
            subscribe_message = {
                "a": "subscribe",
                "v": token_list
            }
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to token: {token_list}")

            # Step 5: Set mode to 'full' to get complete data including market depth
            mode_message = {
                "a": "mode",
                "v": ["full"]
            }
            await self.websocket.send(json.dumps(mode_message))
            logger.info("Set mode to 'full'")

            # Inform the frontend that connection is established
            await self.send(text_data=json.dumps({
                "status": "connected",
                "message": "Connected to m.Stock WebSocket",
                "subscribed_to": token_list,
                'symbol_map': TOKEN_SYMBOL_MAP
            }))
            
            # Step 6: Begin consuming market data
            await self.receive_messages()
            
        except Exception as e:
            logger.info(f"Error in connect: {e}")
            traceback.logger.info_exc()
            
            # Inform the frontend about the error
            await self.send(text_data=json.dumps({
                "status": "error",
                "message": f"Failed to connect: {str(e)}"
            }))

    def decode_binary_message(self, data):
        """
        Decodes binary message from m.Stock WebSocket according to the API documentation.
        The binary message format is:
        - First 2 bytes (short): Number of packets
        - Next 2 bytes (short): Number of total bytes in the quote packet
        - Remaining bytes: Quote packet data
        """
        try:
            # logger.info the full binary data for debugging
            logger.info(f"Raw binary data (length={len(data)}): {data[:50]}...")
            
            if len(data) < 4:
                return {"error": "Data too short to contain header", "raw": list(data)}

            # Extract header (first 4 bytes)
            packet_count, bytes_in_packet = struct.unpack_from('>HH', data, 0)
            logger.info(f"Packet count: {packet_count}, Bytes per packet: {bytes_in_packet}")
            
            if len(data) < 4 + bytes_in_packet:
                logger.info(f"Warning: Data too short (expected {bytes_in_packet} bytes, got {len(data) - 4})")
                return {"error": "Incomplete data", "raw": list(data[:20])}  # Show first 20 bytes only
            
            decoded_packets = []
            offset = 4  # Skip header
            
            for i in range(packet_count):
                logger.info(f"Processing packet {i+1}/{packet_count}, offset: {offset}")
                
                # Check available bytes for this packet
                remaining_bytes = len(data) - offset
                logger.info(f"Remaining bytes: {remaining_bytes}")
                
                if remaining_bytes < 32:  # Minimum packet size (index packet)
                    logger.info(f"Packet too small at offset {offset}: only {remaining_bytes} bytes")
                    break
                
                # Let's examine the first few integer values to help debug
                try:
                    first_values = struct.unpack_from('>4i', data, offset)
                    logger.info(f"First 4 integer values: {first_values}")
                except Exception as e:
                    logger.info(f"Could not unpack first values: {e}")
                
                # Determine if we have a full packet or a partial one
                is_index_packet = False
                
                # If the packet is too short for a quote but enough for an index
                if remaining_bytes < 64 and remaining_bytes >= 32:
                    is_index_packet = True
                    logger.info("Treating as index packet")
                
                if is_index_packet:
                    # Process as Index Packet (32 bytes)
                    try:
                        token, ltp, high, low, open_price, close, price_change, exchange_timestamp = struct.unpack_from('>8i', data, offset)
                        
                        decoded_packets.append({
                            "type": "index",
                            "token": token,
                            "ltp": ltp/100.0,
                            "high": high/100.0,
                            "low": low/100.0,
                            "open": open_price/100.0,
                            "close": close/100.0,
                            "price_change": price_change/100.0,
                            "exchange_timestamp": exchange_timestamp
                        })
                        
                        offset += 32
                    except Exception as e:
                        logger.info(f"Error decoding index packet: {e}")
                        break
                
                else:
                    # Process as regular Quote Packet (64 bytes + Market Depth)
                    try:
                        if remaining_bytes < 64:
                            logger.info(f"Quote packet too short at offset {offset}: only {remaining_bytes} bytes")
                            break
                        
                        # Extract the main quote packet data (64 bytes)
                        (token, ltp, last_traded_qty, avg_price, volume, total_buy_qty, total_sell_qty,
                         open_price, high, low, close, last_traded_ts, open_interest, oi_high, oi_low, 
                         exchange_ts) = struct.unpack_from('>16i', data, offset)
                        
                        packet_data = {
                            "type": "quote",
                            "token": token,
                            "ltp": ltp/100.0,
                            "last_traded_qty": last_traded_qty,
                            "avg_traded_price": avg_price/100.0,
                            "volume_traded_today": volume,
                            "total_buy_qty": total_buy_qty,
                            "total_sell_qty": total_sell_qty,
                            "open": open_price/100.0,
                            "high": high/100.0,
                            "low": low/100.0,
                            "close": close/100.0,
                            "last_traded_timestamp": last_traded_ts,
                            "open_interest": open_interest,
                            "open_interest_high": oi_high,
                            "open_interest_low": oi_low,
                            "exchange_timestamp": exchange_ts
                        }
                        
                        # Check if we have market depth data (additional 120 bytes)
                        if remaining_bytes >= 64 + 120:
                            logger.info("Processing market depth data")
                            depth_offset = offset + 64
                            
                            # Process bid data (5 levels)
                            bids = []
                            for level in range(5):
                                bid_offset = depth_offset + level * 12
                                try:
                                    qty, price, num_orders, _ = struct.unpack_from('>iihh', data, bid_offset)
                                    bids.append({
                                        "quantity": qty,
                                        "price": price/100.0,
                                        "orders": num_orders
                                    })
                                except Exception as e:
                                    logger.info(f"Error unpacking bid level {level}: {e}")
                            
                            # Process ask data (5 levels)
                            asks = []
                            for level in range(5):
                                ask_offset = depth_offset + 60 + level * 12  # 60 bytes for all bids
                                try:
                                    qty, price, num_orders, _ = struct.unpack_from('>iihh', data, ask_offset)
                                    asks.append({
                                        "quantity": qty,
                                        "price": price/100.0,
                                        "orders": num_orders
                                    })
                                except Exception as e:
                                    logger.info(f"Error unpacking ask level {level}: {e}")
                            
                            packet_data["market_depth"] = {
                                "bids": bids,
                                "asks": asks
                            }
                        else:
                            logger.info(f"Not enough data for market depth. Have {remaining_bytes} bytes, need {64+120}")
                        
                        decoded_packets.append(packet_data)
                        logger.info(f"Successfully decoded quote packet with token {token}")
                        offset += bytes_in_packet
                    
                    except Exception as e:
                        logger.info(f"Error decoding quote packet: {e}")
                        traceback.logger.info_exc()
                        break
            
            result = decoded_packets if decoded_packets else {"note": "No packets decoded"}
            logger.info(f"Final decoded result: {json.dumps(result, indent=2)[:200]}...")
            return result
            
        except Exception as e:
            logger.info(f"Error decoding binary message: {e}")
            traceback.logger.info_exc()
            return {"error": str(e), "raw": list(data[:30])}  # Show first 30 bytes

    async def receive_messages(self):
        try:
            while True:
                response = await self.websocket.recv()
                logger.info(f"Received message type: {type(response)}")
                
                if isinstance(response, bytes):
                    decoded = self.decode_binary_message(response)
                    # Send to the frontend
                    try:
                        logger.info("Sending decoded data to frontend")
                        await self.send(text_data=json.dumps(decoded))
                        logger.info("Data sent successfully")
                    except Exception as e:
                        logger.info(f"Error sending data to frontend: {e}")
                        traceback.logger.info_exc()
                else:
                    logger.info(f"Received text: {response}")
                    try:
                        await self.send(text_data=json.dumps({"text_message": response}))
                    except Exception as e:
                        logger.info(f"Error sending text message to frontend: {e}")
        except websockets.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.info(f"Error in receive_messages: {e}")
            traceback.logger.info_exc()

    async def disconnect(self, close_code):
        try:
            # Send unsubscribe request for all subscribed tokens
            unsubscribe_message = {
                "a": "unsubscribe",
                "v": token_list  # Use the same tokens used in subscription
            }
            await self.websocket.send(json.dumps(unsubscribe_message))
        except Exception as e:
            logger.info("Error while unsubscribing or closing socket:", e)
        finally:
            # Ensure the WebSocket is closed
            try:
                await self.websocket.close()
            except:
                pass