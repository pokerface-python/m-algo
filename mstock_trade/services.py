import requests
import json
from datetime import datetime
from django.conf import settings

class MStockAPIService:
    BASE_URL = "https://api.mstock.trade"
    WS_URL = "https://ws.mstock.trade"

    def __init__(self, api_key=None, access_token=None):
        """
        Initialize the MStock API Service
        Args:
            api_key (str): The API key for authentication
            access_token (str): The access token for authentication
        """
        self.api_key = api_key or settings.MSTOCK_API_KEY
        self.access_token = settings.MSTOCK_ACCESS_TOKEN
        self.headers = {
            'X-Mirae-Version': '1',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        if self.access_token:
            self.headers['Authorization'] = f'token {self.api_key}:{self.access_token}'
        if self.api_key:
            self.headers['X-PrivateKey'] = self.api_key

    def _make_request(self, method, endpoint, data=None, params=None):
        """
        Helper method to make authenticated API requests
        """
        if not self.access_token and not endpoint.endswith(('login', 'token')):
            raise ValueError("Access token is required for authenticated endpoints")
            
        try:
            response = requests.request(
                method,
                endpoint,
                json=data if data else None,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error for {endpoint}: {str(e)}")  # Debug print
            return {
                'status': 'false',
                'message': f'API Error: {str(e)}'
            }
        except Exception as e:
            print(f"General Error for {endpoint}: {str(e)}")  # Debug print
            return {
                'status': 'false',
                'message': f'Error: {str(e)}'
            }

    def login(self, username, password):
        """
        First step of login - Get OTP
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/connect/login"
        data = {
            'username': username,
            'password': password
        }
        
        try:
            response = requests.post(endpoint, data=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def verify_otp(self, api_key, otp):
        """
        Second step of login - Verify OTP and get access token
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/session/token"
        data = {
            'api_key': api_key,
            'request_token': otp,
            'checksum': 'L'
        }
        
        try:
            response = requests.post(endpoint, data=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def generate_session(self, refresh_token, otp):
        """
        Generate session token using OTP
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/session/token"
        data = {
            'refreshToken': refresh_token,
            'otp': otp
        }
        
        headers = {
            'X-Mirae-Version': '1',
            'Content-Type': 'application/json',
            'X-PrivateKey': self.api_key
        }
        
        print(f"Making session request to {endpoint}")  # Debug print
        print(f"Request headers: {headers}")  # Debug print
        print(f"Request data: {data}")  # Debug print
        
        try:
            response = requests.post(endpoint, json=data, headers=headers)
            print(f"Response status code: {response.status_code}")  # Debug print
            print(f"Response headers: {response.headers}")  # Debug print
            print(f"Response content: {response.text}")  # Debug print
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Session Generation API Error: {str(e)}")  # Debug print
            return {
                'status': 'false',
                'message': f'API Error: {str(e)}'
            }
        except Exception as e:
            print(f"Session Generation General Error: {str(e)}")  # Debug print
            return {
                'status': 'false',
                'message': f'Error: {str(e)}'
            }

    def get_fund_summary(self):
        """
        Get user's fund summary including cash balance and margin information
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/user/fundsummary"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching fund summary: {str(e)}")

    def get_positions(self):
        """
        Get user positions
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/portfolio/positions"
        return self._make_request('GET', endpoint)

        # endpoint = f"{self.BASE_URL}/openapi/typeb/portfolio/positions"
        # return self._make_request('GET', endpoint)

    def get_portfolio_summary(self):
        """
        Get portfolio summary
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/user/fundsummary"
        return self._make_request('GET', endpoint)

    def place_order(self, trading_symbol, exchange, transaction_type, order_type, quantity, product, validity="DAY", price=None, trigger_price=None, disclosed_quantity=0):
        """
        Place an order on mStock
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/orders/regular"
        data = {
            'tradingsymbol': trading_symbol,
            'exchange': exchange,
            'transaction_type': transaction_type,
            'order_type': order_type,
            'quantity': quantity,
            'product': product,
            'validity': validity,
            'disclosed_quantity': disclosed_quantity
        }
        
        if price:
            data['price'] = price
        if trigger_price:
            data['trigger_price'] = trigger_price
            
        return self._make_request('POST', endpoint, data=data)

    def modify_order(self, order_id, trading_symbol, exchange, transaction_type, order_type, quantity, product, validity="DAY", price=None, trigger_price=None):
        """
        Modify an existing order
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/orders/regular/{order_id}"
        data = {
            'tradingsymbol': trading_symbol,
            'exchange': exchange,
            'transaction_type': transaction_type,
            'order_type': order_type,
            'quantity': quantity,
            'product': product,
            'validity': validity
        }
        
        if price:
            data['price'] = price
        if trigger_price:
            data['trigger_price'] = trigger_price
            
        return self._make_request('PUT', endpoint, data=data)

    def cancel_order(self, order_id):
        """
        Cancel an existing order
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/orders/regular/{order_id}"
        return self._make_request('DELETE', endpoint)

    def cancel_all_orders(self):
        """
        Cancel all pending orders
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/orders/cancelall"
        try:
            response = requests.post(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error canceling all orders: {str(e)}")

    def get_order_book(self):
        """
        Get all orders for the day
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/orders"
        return self._make_request('GET', endpoint)

    def get_trade_history(self, from_date=None, to_date=None):
        """
        Get trade history for a date range
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/trades"
        params = {}
        if from_date:
            params['fromdate'] = from_date
        if to_date:
            params['todate'] = to_date
        return self._make_request('GET', endpoint, params=params)

    def get_order_details(self, order_id, segment="E"):
        """
        Get details of a specific order
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/order/details"
        data = {
            'order_no': order_id,
            'segment': segment
        }
        try:
            response = requests.post(endpoint, headers=self.headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching order details: {str(e)}")

    def get_market_quote(self, symbol):
        """
        Get market quote for a symbol
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/quotes/{symbol}"
        return self._make_request('GET', endpoint)

    def get_portfolio(self):
        """
        Get user's portfolio
        """
        endpoint = f"{self.BASE_URL}/portfolio"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching portfolio: {str(e)}")

    def get_historical_data(self, symbol, interval, start_time, end_time):
        """
        Get historical data for a symbol
        """
        endpoint = f"{self.BASE_URL}/historical"
        params = {
            "symbol": symbol,
            "interval": interval,
            "start_time": start_time,
            "end_time": end_time
        }
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching historical data: {str(e)}")

    def convert_position(self, trading_symbol, exchange, transaction_type, position_type, quantity, old_product, new_product):
        """
        Convert position from one product type to another
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/portfolio/convertposition"
        data = {
            'tradingsymbol': trading_symbol,
            'exchange': exchange,
            'transaction_type': transaction_type,
            'position_type': position_type,
            'quantity': quantity,
            'old_product': old_product,
            'new_product': new_product
        }
        try:
            response = requests.post(endpoint, headers=self.headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error converting position: {str(e)}")

    def get_holdings(self):
        """
        Get all holdings in the user's portfolio
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/portfolio/holdings"
        return self._make_request('GET', endpoint)

    def get_holding_details(self, trading_symbol):
        """
        Get detailed information about a specific holding
        """
        holdings = self.get_holdings()
        if holdings.get('status') != 'success':
            raise Exception("Failed to fetch holdings data")

        for holding in holdings.get('data', []):
            if holding.get('tradingsymbol') == trading_symbol:
                return holding
        return None

    def get_market_ohlc(self, instruments):
        """
        Get OHLC (Open, High, Low, Close) market data for specified instruments
        Args:
            instruments (list): List of instruments in format ['NSE:ACC', 'BSE:ACC']
        Returns:
            dict: OHLC data for the instruments
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/instruments/quote/ohlc"
        params = {'i': instruments}
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching OHLC data: {str(e)}")

    def get_market_ltp(self, instruments):
        """
        Get Last Traded Price (LTP) for specified instruments
        Args:
            instruments (list): List of instruments in format ['NSE:ACC', 'BSE:ACC']
        Returns:
            dict: LTP data for the instruments
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/instruments/quote/ltp"
        params = {'i': instruments}
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching LTP data: {str(e)}")

    def get_instrument_master(self):
        """
        Fetch instrument master data from the API
        Returns:
            dict: Dictionary containing status and parsed CSV data
        """
        try:
            url = f"{self.BASE_URL}/openapi/typea/instruments/scriptmaster"
            headers = {
                'X-Mirae-Version': '1',
                'Authorization': f'token {self.api_key}:{self.access_token}'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = response.text.strip().split('\n')
            headers = csv_data[0].split(',')
            instruments = []
            
            for row in csv_data[1:]:
                values = row.split(',')
                instrument = dict(zip(headers, values))
                instruments.append(instrument)
            
            return {
                'status': 'success',
                'data': instruments
            }
            
        except Exception as e:
            print(f"Error fetching instrument master: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def get_market_quote_batch(self, instruments):
        """
        Get comprehensive market quote data for multiple instruments
        Args:
            instruments (list): List of instruments in format ['NSE:ACC', 'BSE:ACC']
        Returns:
            dict: Combined OHLC and LTP data for the instruments
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/quotes/batch"
        data = {'instruments': instruments}
        return self._make_request('POST', endpoint, data=data)

    def get_market_quote_single(self, instrument):
        """
        Get comprehensive market quote data for a single instrument
        Args:
            instrument (str): Instrument in format 'NSE:ACC'
        Returns:
            dict: Combined OHLC and LTP data for the instrument
        """
        return self.get_market_quote_batch([instrument])

    def get_historical_data(self, instrument_token, interval, from_date, to_date):
        """
        Get historical candle data for an instrument
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/instruments/historical/{instrument_token}/{interval}"
        params = {
            'from': from_date,
            'to': to_date
        }
        return self._make_request('GET', endpoint, params=params)

    def get_historical_data_formatted(self, instrument_token, interval, from_date, to_date):
        """
        Get historical data with formatted candles
        Args:
            instrument_token (int): The instrument token
            interval (str): Time interval
            from_date (str): Start date
            to_date (str): End date
        Returns:
            dict: Formatted historical data with OHLCV candles
        """
        data = self.get_historical_data(instrument_token, interval, from_date, to_date)
        if data.get('status') != 'success':
            raise Exception("Failed to fetch historical data")

        formatted_candles = []
        for candle in data.get('data', {}).get('candles', []):
            formatted_candles.append({
                'timestamp': candle[0],
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4],
                'volume': candle[5]
            })

        return {
            'status': 'success',
            'data': {
                'candles': formatted_candles,
                'interval': interval,
                'instrument_token': instrument_token
            }
        }

    def get_option_chain_master(self, exchange):
        """
        Get option chain master data for an exchange
        Args:
            exchange (int): Exchange ID (2 for NSE)
        Returns:
            dict: Option chain master data including expiry dates and available instruments
        """
        endpoint = f"{self.BASE_URL}/openapi/typea/getoptionchainmaster/{exchange}"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching option chain master: {str(e)}")

    def get_option_chain(self, exchange, expiry, token):
        """
        Get option chain data for a specific instrument
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/optionchain/{exchange}/{expiry}/{token}"
        return self._make_request('GET', endpoint)

    def get_option_chain_formatted(self, exchange, expiry, token):
        """
        Get formatted option chain data with parsed values
        Args:
            exchange (int): Exchange ID (2 for NSE)
            expiry (int): Expiry timestamp
            token (int): Instrument token
        Returns:
            dict: Formatted option chain data with parsed values
        """
        data = self.get_option_chain(exchange, expiry, token)
        if data.get('status') != 'success':
            raise Exception("Failed to fetch option chain data")

        formatted_data = {
            'status': 'success',
            'data': {
                'contract': data.get('data', {}).get('contractModel', {}),
                'calls': [],
                'puts': [],
                'future': None,
                'spot': None
            }
        }

        # Parse call options
        for call in data.get('data', {}).get('call', []):
            parts = call.split(',')
            if len(parts) >= 3:
                formatted_data['data']['calls'].append({
                    'token': parts[0],
                    'strike': float(parts[1]) / 100,  # Convert to actual price
                    'oi': int(parts[2])
                })

        # Parse put options
        for put in data.get('data', {}).get('put', []):
            parts = put.split(',')
            if len(parts) >= 3:
                formatted_data['data']['puts'].append({
                    'token': parts[0],
                    'strike': float(parts[1]) / 100,  # Convert to actual price
                    'oi': int(parts[2])
                })

        # Parse future data
        future = data.get('data', {}).get('future', [])
        if future and len(future) > 0:
            parts = future[0].split(',')
            if len(parts) >= 3:
                formatted_data['data']['future'] = {
                    'token': parts[0],
                    'price': float(parts[2]) / 100 if parts[2] != '-1' else None
                }

        # Parse spot data
        spot = data.get('data', {}).get('spot', '')
        if spot:
            parts = spot.split(',')
            if len(parts) >= 3:
                formatted_data['data']['spot'] = {
                    'symbol': parts[0],
                    'token': parts[1],
                    'exchange': parts[2]
                }

        return formatted_data

    def get_intraday_data(self, exchange, script_name, interval):
        """
        Get intraday chart data for an instrument
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/instruments/intraday/{exchange}/{script_name}/{interval}"
        return self._make_request('GET', endpoint)

    def get_intraday_data_formatted(self, exchange, script_name, interval):
        """
        Get formatted intraday chart data
        Args:
            exchange (int): Exchange ID
            script_name (str): Script name
            interval (str): Time interval
        Returns:
            dict: Formatted intraday data with OHLCV candles
        """
        data = self.get_intraday_data(exchange, script_name, interval)
        if data.get('status') != 'success':
            raise Exception("Failed to fetch intraday data")

        formatted_candles = []
        for candle in data.get('data', {}).get('candles', []):
            formatted_candles.append({
                'timestamp': candle[0],
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4],
                'volume': candle[5]
            })

        return {
            'status': 'success',
            'data': {
                'candles': formatted_candles,
                'interval': interval,
                'exchange': exchange,
                'script_name': script_name
            }
        }

    def get_gainers_losers(self, exchange, security_id_code, segment, type_flag):
        """
        Get top gainers or losers for a given exchange and segment
        """
        endpoint = f"{self.BASE_URL}/openapi/typeb/market/gainers-losers"
        data = {
            'exchange': str(exchange),
            'security_id_code': str(security_id_code),
            'segment': str(segment),
            'type': type_flag
        }
        return self._make_request('POST', endpoint, data=data)

    def get_gainers_losers_formatted(self, exchange, security_id_code, segment, type_flag):
        """
        Get formatted gainers/losers data
        Args:
            exchange (int): Exchange ID
            security_id_code (int): Security ID Code
            segment (int): Segment ID
            type_flag (str): 'G' for Gainers, 'L' for Losers
        Returns:
            dict: Formatted gainers/losers data
        """
        data = self.get_gainers_losers(exchange, security_id_code, segment, type_flag)
        if data.get('status') != True:
            raise Exception("Failed to fetch gainers/losers data")

        formatted_data = []
        for item in data.get('data', []):
            formatted_data.append({
                'symbol': item.get('symbol'),
                'symbol_name': item.get('symbol_name'),
                'last_price': item.get('ltp'),
                'change': item.get('change'),
                'percent_change': item.get('per_change'),
                'volume': item.get('volume'),
                'open': item.get('Open'),
                'high': item.get('Price1'),
                'low': item.get('Price'),
                'previous_close': item.get('Pclose'),
                'exchange': item.get('exchange'),
                'segment': item.get('segment'),
                'instrument': item.get('instrument'),
                'series': item.get('series'),
                'lot_size': item.get('lot_size')
            })

        return {
            'status': 'success',
            'data': formatted_data,
            'type': 'gainers' if type_flag == 'G' else 'losers'
        } 