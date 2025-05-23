from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Strategy, Trade, APIKeys, Position, Order, Instrument
from .services import MStockAPIService
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime
from django.views.decorators.http import require_http_methods
import json
from functools import wraps

def access_token_required(view_func):
    """
    Custom decorator that checks for access_token in session
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('access_token'):
            messages.error(request, 'Please login to continue')
            return redirect('mstock_trade:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@access_token_required
def home(request):
    """
    Home view that serves as the main landing page
    """
    return render(request, 'mstock_trade/home.html')

@access_token_required
def dashboard(request):
    """
    Dashboard view that displays trading information
    """
    try:
        # Initialize API service with session token
        api_service = MStockAPIService(access_token=request.session['access_token'])
        
        # Get user_id from session
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'User session not found')
            return redirect('mstock_trade:login')
        
        # Get user's strategies
        strategies = Strategy.objects.filter(user_id=user_id)
        
        # Get recent trades
        trades = Trade.objects.filter(strategy__user_id=user_id).order_by('-executed_at')[:10]
        
        # Get positions
        positions = Position.objects.filter(user_id=user_id)
        
        # Get orders
        orders = Order.objects.filter(user_id=user_id, status='PENDING')
        
        return render(request, 'mstock_trade/dashboard.html', {
            'strategies': strategies,
            'trades': trades,
            'positions': positions,
            'orders': orders,
            'user_name': request.session.get('user_name', ''),
            'access_token': request.session.get('access_token', ''),
            'user_id': user_id
        })
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('mstock_trade:login')

@access_token_required
def create_strategy(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        user_id = request.session.get('user_id')
        
        strategy = Strategy.objects.create(
            name=name,
            description=description,
            user_id=user_id
        )
        messages.success(request, 'Strategy created successfully!')
        return redirect('mstock_trade:dashboard')
    
    return render(request, 'mstock_trade/create_strategy.html')

@access_token_required
def execute_trade(request):
    if request.method == 'POST':
        try:
            strategy_id = request.POST.get('strategy_id')
            symbol = request.POST.get('symbol')
            quantity = int(request.POST.get('quantity'))
            order_type = request.POST.get('order_type')
            user_id = request.session.get('user_id')
            
            strategy = Strategy.objects.get(id=strategy_id, user_id=user_id)
            
            # Initialize API service
            api_service = MStockAPIService(access_token=request.session['access_token'])
            
            # Place order
            order_response = api_service.place_order(symbol, quantity, order_type)
            
            # Create trade record
            trade = Trade.objects.create(
                strategy=strategy,
                symbol=symbol,
                quantity=quantity,
                price=order_response.get('price', 0),
                trade_type=order_type,
                status='EXECUTED'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Trade executed successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@access_token_required
def get_market_data(request):
    symbol = request.GET.get('symbol')
    try:
        api_service = MStockAPIService(access_token=request.session['access_token'])
        market_data = api_service.get_market_quote(symbol)
        return JsonResponse(market_data)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@access_token_required
def position_list(request):
    """
    View to display all positions for the logged-in user
    """
    try:
        api_service = MStockAPIService(access_token=request.session['access_token'])
        positions_data = api_service.get_positions()

        if positions_data.get('status') != 'success':
            messages.error(request, positions_data.get('message', 'Error fetching positions'))
            return redirect('mstock_trade:dashboard')

        user_id = request.session.get('user_id')
        net_positions = positions_data.get('data', {}).get('net', [])

        for position_data in net_positions:
            Position.objects.update_or_create(
                user_id=user_id,
                trading_symbol=position_data['tradingsymbol'],
                exchange=position_data['exchange'],
                defaults={
                    'quantity': position_data['quantity'],
                    'average_price': position_data['average_price'],
                    'product': position_data['product'],
                    # 'position_type': '',  # You can decide how to derive or remove this
                    'pnl': position_data.get('pnl', 0),
                    'm2m': position_data.get('m2m', 0),
                    'unrealized_pnl': position_data.get('unrealised', 0),
                    'realized_pnl': position_data.get('realised', 0)
                }
            )

        positions = Position.objects.filter(user_id=user_id)
        return render(request, 'mstock_trade/position_list.html', {'positions': positions})
    except Exception as e:
        messages.error(request, f"Error fetching positions: {str(e)}")
        return redirect('mstock_trade:dashboard')




# @access_token_required
# def position_list(request):
#     """
#     View to display all positions for the logged-in user
#     """
#     try:
#         # Initialize API service with session token
#         api_service = MStockAPIService(access_token=request.session['access_token'])
#         breakpoint()
#         # Get positions from API
#         positions_data = api_service.get_positions()
        
#         if positions_data.get('status') != 'true':
#             messages.error(request, positions_data.get('message', 'Error fetching positions'))
#             return redirect('mstock_trade:dashboard')
        
#         # Update local database with latest position data
#         user_id = request.session.get('user_id')
#         for position_data in positions_data.get('data', []):
#             Position.objects.update_or_create(
#                 user_id=user_id,
#                 trading_symbol=position_data['tradingsymbol'],
#                 exchange=position_data['exchange'],
#                 defaults={
#                     'quantity': position_data['quantity'],
#                     'average_price': position_data['average_price'],
#                     'product': position_data['product'],
#                     'position_type': position_data['position_type'],
#                     'pnl': position_data.get('pnl', 0),
#                     'm2m': position_data.get('m2m', 0),
#                     'unrealized_pnl': position_data.get('unrealized_pnl', 0),
#                     'realized_pnl': position_data.get('realized_pnl', 0)
#                 }
#             )
        
#         # Get positions from local database
#         positions = Position.objects.filter(user_id=user_id)
#         return render(request, 'mstock_trade/position_list.html', {'positions': positions})
#     except Exception as e:
#         messages.error(request, f"Error fetching positions: {str(e)}")
#         return redirect('mstock_trade:dashboard')

@access_token_required
def convert_position(request):
    """
    View to handle position conversion
    """
    if request.method == 'POST':
        try:
            api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
            response = api_service.convert_position(
                trading_symbol=request.POST['trading_symbol'],
                exchange=request.POST['exchange'],
                transaction_type=request.POST['transaction_type'],
                position_type=request.POST['position_type'],
                quantity=int(request.POST['quantity']),
                old_product=request.POST['old_product'],
                new_product=request.POST['new_product']
            )
            messages.success(request, "Position converted successfully")
            return redirect('mstock_trade:position_list')
        except Exception as e:
            messages.error(request, f"Error converting position: {str(e)}")
            return redirect('mstock_trade:position_list')
    
    # Get available positions for conversion
    positions = Position.objects.filter(user=request.session.get('user_id'))
    return render(request, 'mstock_trade/convert_position.html', {'positions': positions})

@access_token_required
def order_book(request):
    """
    View to display all orders for the day
    """
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        orders = api_service.get_order_book()
        return render(request, 'mstock_trade/order_book.html', {'orders': orders.get('data', [])})
    except Exception as e:
        messages.error(request, f"Error fetching orders: {str(e)}")
        return redirect('mstock_trade:dashboard')

@access_token_required
def trade_history(request):
    """
    View to display trade history
    """
    try:
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        trades = api_service.get_trade_history(from_date, to_date)
        return render(request, 'mstock_trade/trade_history.html', {'trades': trades.get('data', [])})
    except Exception as e:
        messages.error(request, f"Error fetching trade history: {str(e)}")
        return redirect('mstock_trade:dashboard')

@access_token_required
def place_order(request):
    """
    View to handle order placement
    """
    if request.method == 'POST':
        try:
            api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
            response = api_service.place_order(
                trading_symbol=request.POST['trading_symbol'],
                exchange=request.POST['exchange'],
                transaction_type=request.POST['transaction_type'],
                order_type=request.POST['order_type'],
                quantity=int(request.POST['quantity']),
                product=request.POST['product'],
                validity=request.POST.get('validity', 'DAY'),
                price=float(request.POST['price']) if request.POST.get('price') else None,
                trigger_price=float(request.POST['trigger_price']) if request.POST.get('trigger_price') else None,
                disclosed_quantity=int(request.POST['disclosed_quantity']) if request.POST.get('disclosed_quantity') else 0
            )
            messages.success(request, "Order placed successfully")
            return redirect('mstock_trade:order_book')
        except Exception as e:
            messages.error(request, f"Error placing order: {str(e)}")
            return redirect('mstock_trade:place_order')
    
    return render(request, 'mstock_trade/place_order.html')

@access_token_required
def modify_order(request, order_id):
    """
    View to handle order modification
    """
    if request.method == 'POST':
        try:
            api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
            response = api_service.modify_order(
                order_id=order_id,
                trading_symbol=request.POST['trading_symbol'],
                exchange=request.POST['exchange'],
                transaction_type=request.POST['transaction_type'],
                order_type=request.POST['order_type'],
                quantity=int(request.POST['quantity']),
                product=request.POST['product'],
                validity=request.POST.get('validity', 'DAY'),
                price=float(request.POST['price']) if request.POST.get('price') else None,
                trigger_price=float(request.POST['trigger_price']) if request.POST.get('trigger_price') else None
            )
            messages.success(request, "Order modified successfully")
            return redirect('mstock_trade:order_book')
        except Exception as e:
            messages.error(request, f"Error modifying order: {str(e)}")
            return redirect('mstock_trade:order_book')
    
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        order_details = api_service.get_order_details(order_id)
        return render(request, 'mstock_trade/modify_order.html', {'order': order_details.get('data', [])[0]})
    except Exception as e:
        messages.error(request, f"Error fetching order details: {str(e)}")
        return redirect('mstock_trade:order_book')

@access_token_required
def cancel_order(request, order_id):
    """
    View to handle order cancellation
    """
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        response = api_service.cancel_order(order_id)
        messages.success(request, "Order cancelled successfully")
    except Exception as e:
        messages.error(request, f"Error cancelling order: {str(e)}")
    return redirect('mstock_trade:order_book')

@access_token_required
def cancel_all_orders(request):
    """
    View to handle cancellation of all orders
    """
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        response = api_service.cancel_all_orders()
        messages.success(request, "All orders cancelled successfully")
    except Exception as e:
        messages.error(request, f"Error cancelling all orders: {str(e)}")
    return redirect('mstock_trade:order_book')

@access_token_required
def portfolio(request):
    """
    View to display portfolio holdings and summary
    """
    try:
        api_service = MStockAPIService(access_token=request.session['access_token'])
        
        holdings = api_service.get_holdings()
        portfolio_summary = api_service.get_portfolio_summary()
        
        if holdings.get('status') != 'true' or portfolio_summary.get('status') != 'true':
            messages.error(request, 'Error fetching portfolio data')
            return redirect('mstock_trade:dashboard')
        
        return render(request, 'mstock_trade/portfolio.html', {
            'holdings': holdings.get('data', []),
            'summary': portfolio_summary.get('data', {})
        })
    except Exception as e:
        messages.error(request, f"Error fetching portfolio: {str(e)}")
        return redirect('mstock_trade:dashboard')

@access_token_required
def holding_details(request, trading_symbol):
    """
    View to display detailed information about a specific holding
    """
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        holding = api_service.get_holding_details(trading_symbol)
        
        if not holding:
            messages.error(request, f"Holding not found for symbol: {trading_symbol}")
            return redirect('mstock_trade:portfolio')
        
        return render(request, 'mstock_trade/holding_details.html', {'holding': holding})
    except Exception as e:
        messages.error(request, f"Error fetching holding details: {str(e)}")
        return redirect('mstock_trade:portfolio')

@access_token_required
def market_quote(request):
    """
    View to display market quotes for selected instruments
    """
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        
        # Get instruments from query parameters or default to some popular ones
        instruments = request.GET.getlist('instruments', ['NSE:NIFTY', 'NSE:BANKNIFTY'])
        
        # Get market data
        market_data = api_service.get_market_quote_batch(instruments)
        
        # Get instrument master for dropdown
        instrument_master = api_service.get_instrument_master()
        
        return render(request, 'mstock_trade/market_quote.html', {
            'market_data': market_data.get('data', {}),
            'instruments': instruments,
            'instrument_master': instrument_master.get('data', {})
        })
    except Exception as e:
        messages.error(request, f"Error fetching market quotes: {str(e)}")
        return redirect('mstock_trade:dashboard')

@access_token_required
def instrument_search(request):
    """
    View to search and select instruments
    """
    try:
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        instrument_master = api_service.get_instrument_master()
        
        search_query = request.GET.get('q', '')
        if search_query:
            # Filter instruments based on search query
            filtered_instruments = {
                k: v for k, v in instrument_master.get('data', {}).items()
                if search_query.lower() in k.lower()
            }
        else:
            filtered_instruments = instrument_master.get('data', {})
        
        return render(request, 'mstock_trade/instrument_search.html', {
            'instruments': filtered_instruments,
            'search_query': search_query
        })
    except Exception as e:
        messages.error(request, f"Error searching instruments: {str(e)}")
        return redirect('mstock_trade:dashboard')

@access_token_required
def market_quote_ajax(request):
    """
    AJAX endpoint to get real-time market quotes
    """
    try:
        instruments = request.GET.getlist('instruments', [])
        if not instruments:
            return JsonResponse({'status': 'error', 'message': 'No instruments specified'})
        
        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        market_data = api_service.get_market_quote_batch(instruments)
        
        return JsonResponse(market_data)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@access_token_required
def historical_data(request):
    """
    View to display historical data for an instrument
    """
    try:
        instrument_token = request.GET.get('instrument_token')
        interval = request.GET.get('interval', 'day')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if not all([instrument_token, from_date, to_date]):
            messages.warning(request, "Please provide all required parameters")
            return redirect('mstock_trade:market_quote')

        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        historical_data = api_service.get_historical_data_formatted(
            instrument_token=instrument_token,
            interval=interval,
            from_date=from_date,
            to_date=to_date
        )

        # Get instrument details for display
        instrument_master = api_service.get_instrument_master()
        instrument_details = next(
            (details for symbol, details in instrument_master.get('data', {}).items()
             if str(details.get('instrument_token')) == str(instrument_token)),
            None
        )

        return render(request, 'mstock_trade/historical_data.html', {
            'historical_data': historical_data.get('data', {}),
            'instrument_details': instrument_details,
            'interval': interval,
            'from_date': from_date,
            'to_date': to_date
        })
    except Exception as e:
        messages.error(request, f"Error fetching historical data: {str(e)}")
        return redirect('mstock_trade:market_quote')

@access_token_required
def historical_data_ajax(request):
    """
    AJAX endpoint to get historical data
    """
    try:
        instrument_token = request.GET.get('instrument_token')
        interval = request.GET.get('interval', 'day')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if not all([instrument_token, from_date, to_date]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required parameters'
            })

        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        historical_data = api_service.get_historical_data_formatted(
            instrument_token=instrument_token,
            interval=interval,
            from_date=from_date,
            to_date=to_date
        )

        return JsonResponse(historical_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@access_token_required
def option_chain(request):
    """
    View to display option chain for a selected instrument
    """
    try:
        exchange = request.GET.get('exchange', '2')  # Default to NSE
        expiry = request.GET.get('expiry')
        token = request.GET.get('token')

        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        
        # Get option chain master data
        master_data = api_service.get_option_chain_master(exchange)
        
        # If expiry and token are provided, get option chain data
        option_chain_data = None
        if expiry and token:
            option_chain_data = api_service.get_option_chain_formatted(exchange, expiry, token)

        return render(request, 'mstock_trade/option_chain.html', {
            'master_data': master_data.get('data', {}),
            'option_chain': option_chain_data.get('data') if option_chain_data else None,
            'selected_exchange': exchange,
            'selected_expiry': expiry,
            'selected_token': token
        })
    except Exception as e:
        messages.error(request, f"Error fetching option chain: {str(e)}")
        return redirect('mstock_trade:dashboard')

@access_token_required
def option_chain_ajax(request):
    """
    AJAX endpoint to get option chain data
    """
    try:
        exchange = request.GET.get('exchange', '2')
        expiry = request.GET.get('expiry')
        token = request.GET.get('token')

        if not all([exchange, expiry, token]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required parameters'
            })

        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        option_chain_data = api_service.get_option_chain_formatted(exchange, expiry, token)

        return JsonResponse(option_chain_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@access_token_required
def intraday_chart(request):
    """
    View to display intraday chart for a selected instrument
    """
    try:
        exchange = request.GET.get('exchange', '1')  # Default to NSE
        script_name = request.GET.get('script_name')
        interval = request.GET.get('interval', 'minute')

        if not script_name:
            messages.warning(request, "Please select an instrument")
            return redirect('mstock_trade:market_quote')

        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        
        # Get intraday data
        intraday_data = api_service.get_intraday_data_formatted(exchange, script_name, interval)
        
        # Get instrument details for display
        instrument_master = api_service.get_instrument_master()
        instrument_details = next(
            (details for symbol, details in instrument_master.get('data', {}).items()
             if details.get('name') == script_name),
            None
        )

        return render(request, 'mstock_trade/intraday_chart.html', {
            'intraday_data': intraday_data.get('data', {}),
            'instrument_details': instrument_details,
            'selected_exchange': exchange,
            'selected_script': script_name,
            'selected_interval': interval
        })
    except Exception as e:
        messages.error(request, f"Error fetching intraday data: {str(e)}")
        return redirect('mstock_trade:market_quote')

@access_token_required
def intraday_chart_ajax(request):
    """
    AJAX endpoint to get intraday chart data
    """
    try:
        exchange = request.GET.get('exchange', '1')
        script_name = request.GET.get('script_name')
        interval = request.GET.get('interval', 'minute')

        if not script_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Script name is required'
            })

        api_service = MStockAPIService(settings.MSTOCK_API_KEY, settings.MSTOCK_API_SECRET)
        intraday_data = api_service.get_intraday_data_formatted(exchange, script_name, interval)

        return JsonResponse(intraday_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@access_token_required
def gainers_losers(request):
    """
    View to display top gainers and losers
    """
    try:
        exchange = request.GET.get('exchange', '1')  # Default to NSE
        security_id_code = request.GET.get('security_id_code', '13')  # Default to NSE Equity
        segment = request.GET.get('segment', '1')  # Default to Equity segment
        type_flag = request.GET.get('type', 'G')  # Default to Gainers

        api_service = MStockAPIService()
        data = api_service.get_gainers_losers_formatted(
            exchange=exchange,
            security_id_code=security_id_code,
            segment=segment,
            type_flag=type_flag
        )

        context = {
            'data': data['data'],
            'type': data['type'],
            'selected_exchange': exchange,
            'selected_security_id': security_id_code,
            'selected_segment': segment,
            'selected_type': type_flag
        }
        return render(request, 'mstock_trade/gainers_losers.html', context)

    except Exception as e:
        messages.error(request, str(e))
        return redirect('mstock_trade:market_quote')

@access_token_required
def gainers_losers_ajax(request):
    """
    AJAX endpoint to get gainers/losers data
    """
    try:
        exchange = request.GET.get('exchange', '1')
        security_id_code = request.GET.get('security_id_code', '13')
        segment = request.GET.get('segment', '1')
        type_flag = request.GET.get('type', 'G')

        api_service = MStockAPIService()
        data = api_service.get_gainers_losers_formatted(
            exchange=exchange,
            security_id_code=security_id_code,
            segment=segment,
            type_flag=type_flag
        )

        return JsonResponse({
            'status': 'success',
            'data': data['data'],
            'type': data['type']
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@require_http_methods(["GET", "POST"])
def mstock_login(request):
    """
    Handle the initial login request to get OTP
    """
    # Store the next URL if it exists
    next_url = request.GET.get('next')
    if next_url:
        request.session['next_url'] = next_url

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            api_service = MStockAPIService()
            # First login attempt to get OTP
            response = api_service.login(username, password)
            
            if response.get('status') == 'success':
                # Store only the API key in session for OTP verification
                request.session['api_key'] = settings.MSTOCK_API_KEY
                
                messages.success(request, 'Please enter the OTP sent to your registered mobile number')
                return redirect('mstock_trade:verify_otp')
            else:
                messages.error(request, response.get('message', 'Login failed'))
                return redirect('mstock_trade:login')
                
        except Exception as e:
            messages.error(request, f"Login error: {str(e)}")
            return redirect('mstock_trade:login')
    
    return render(request, 'mstock_trade/mstock_login.html')

@require_http_methods(["GET", "POST"])
def mstock_verify_otp(request):
    """
    Handle OTP verification and session generation
    """
    if 'api_key' not in request.session:
        messages.error(request, 'Please login first')
        return redirect('mstock_trade:login')
    
    if request.method == "POST":
        otp = request.POST.get('otp')
        
        try:
            api_service = MStockAPIService()
            # Verify OTP and get access token
            response = api_service.verify_otp(
                api_key=request.session['api_key'],
                otp=otp
            )
            
            if response.get('status') == 'success':
                # Store all necessary tokens in session
                request.session['access_token'] = response['data'].get('access_token')
                request.session['refresh_token'] = response['data'].get('refresh_token')
                request.session['public_token'] = response['data'].get('public_token')
                request.session['user_id'] = response['data'].get('user_id')
                request.session['user_name'] = response['data'].get('user_name')
                request.session['api_key'] = response['data'].get('api_key')
                
                # Set session expiry (optional, adjust as needed)
                request.session.set_expiry(86400)  # 24 hours
                
                # Clear temporary session data
                if 'api_key' in request.session:
                    del request.session['api_key']
                
                messages.success(request, 'Login successful')
                return redirect('mstock_trade:dashboard')
            else:
                messages.error(request, response.get('message', 'OTP verification failed'))
                return redirect('mstock_trade:verify_otp')
                
        except Exception as e:
            messages.error(request, f"OTP verification error: {str(e)}")
            return redirect('mstock_trade:verify_otp')
    
    return render(request, 'mstock_trade/mstock_otp.html')

def fund_summary_view(request):
    """
    View for displaying user's fund summary
    """
    if not request.session.get('access_token'):
        messages.error(request, 'Please login to view fund summary')
        return redirect('mstock_trade:login')
        
    try:
        api_service = MStockAPIService(
            api_key=settings.MSTOCK_API_KEY,
            api_secret=request.session['access_token']
        )
        response = api_service.get_fund_summary()
        
        if response.get('status') == 'success':
            context = {
                'fund_summary': response['data']
            }
            return render(request, 'mstock_trade/fund_summary.html', context)
        else:
            messages.error(request, response.get('message', 'Failed to fetch fund summary'))
            return redirect('mstock_trade:market_quote')
            
    except Exception as e:
        messages.error(request, str(e))
        return redirect('mstock_trade:market_quote')

def logout_view(request):
    """
    View for handling user logout
    """
    # Clear all session data
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('mstock_trade:login')

def access_info(request):
    """
    View to display access/session information
    """
    return render(request, 'mstock_trade/access_info.html', {
        'access_token': request.session.get('access_token', ''),
        'user_id': request.session.get('user_id', ''),
        'user_name': request.session.get('user_name', ''),
    })

@access_token_required
def sync_instruments(request):
    """
    View to synchronize instrument data from the API
    """
    try:
        # Get API key from settings
        api_key = settings.MSTOCK_API_KEY
        access_token = request.session['access_token']
        
        # Initialize API service with both api_key and access_token
        api_service = MStockAPIService(api_key=api_key, access_token=access_token)
        response = api_service.get_instrument_master()
        
        if response.get('status') == 'error':
            messages.error(request, response.get('message', 'Error fetching instrument data'))
            return redirect('mstock_trade:home')
        
        # Process and save instruments
        instruments_data = response.get('data', [])
        instruments_created = 0
        instruments_updated = 0
        exchange_counts = {}
        segment_counts = {}
        
        # Track unique instrument tokens to prevent duplicates
        processed_tokens = set()
        duplicate_tokens = set()
        
        # First pass: Check for duplicates in the incoming data
        for instrument_data in instruments_data:
            token = instrument_data.get('instrument_token')
            if token in processed_tokens:
                duplicate_tokens.add(token)
            processed_tokens.add(token)
        
        if duplicate_tokens:
            messages.warning(request, f'Found {len(duplicate_tokens)} duplicate instrument tokens in the API response. These will be processed only once.')
        
        # Reset processed tokens for the actual processing
        processed_tokens.clear()
        
        for instrument_data in instruments_data:
            try:
                token = instrument_data.get('instrument_token')
                
                # Skip if we've already processed this token
                if token in processed_tokens:
                    continue
                processed_tokens.add(token)
                
                # Convert empty strings to None
                for key in ['last_price', 'strike', 'tick_size', 'lot_size', 'expiry']:
                    if instrument_data.get(key) == '':
                        instrument_data[key] = None
                
                # Convert numeric values
                if instrument_data.get('last_price'):
                    instrument_data['last_price'] = float(instrument_data['last_price'])
                if instrument_data.get('strike'):
                    instrument_data['strike'] = float(instrument_data['strike'])
                if instrument_data.get('tick_size'):
                    instrument_data['tick_size'] = float(instrument_data['tick_size'])
                if instrument_data.get('lot_size'):
                    instrument_data['lot_size'] = int(instrument_data['lot_size'])
                
                # Convert expiry string to date if present
                if instrument_data.get('expiry'):
                    try:
                        instrument_data['expiry'] = datetime.strptime(instrument_data['expiry'], '%d/%m/%y').date()
                    except ValueError:
                        instrument_data['expiry'] = None
                
                # Check if instrument already exists
                existing_instrument = Instrument.objects.filter(instrument_token=token).first()
                
                # Update or create instrument
                instrument, created = Instrument.objects.update_or_create(
                    instrument_token=token,
                    defaults={
                        'exchange_token': instrument_data['exchange_token'],
                        'trading_symbol': instrument_data['tradingsymbol'],
                        'name': instrument_data['name'],
                        'last_price': instrument_data.get('last_price'),
                        'expiry': instrument_data.get('expiry'),
                        'strike': instrument_data.get('strike'),
                        'tick_size': instrument_data.get('tick_size'),
                        'lot_size': instrument_data.get('lot_size'),
                        'instrument_type': instrument_data['instrument_type'],
                        'segment': instrument_data['segment'],
                        'exchange': instrument_data['exchange']
                    }
                )
                
                if created:
                    instruments_created += 1
                else:
                    instruments_updated += 1
                
                # Count exchanges and segments
                exchange = instrument_data['exchange']
                segment = instrument_data['segment']
                exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
                segment_counts[segment] = segment_counts.get(segment, 0) + 1
                    
            except Exception as e:
                print(f"Error processing instrument {instrument_data.get('tradingsymbol')}: {str(e)}")
                continue
        
        # Verify no duplicates in database
        total_instruments = Instrument.objects.count()
        unique_instruments = Instrument.objects.values('instrument_token').distinct().count()
        
        if total_instruments != unique_instruments:
            messages.error(request, f'Warning: Found {total_instruments - unique_instruments} duplicate records in database!')
        
        # Prepare detailed success message
        success_message = f"""
        ✅ Instrument data successfully synchronized!
        
        📊 Summary:
        - Total instruments processed: {len(instruments_data)}
        - New instruments created: {instruments_created}
        - Existing instruments updated: {instruments_updated}
        - Duplicate tokens in API response: {len(duplicate_tokens)}
        - Total unique instruments in database: {unique_instruments}
        
        📈 Exchange Distribution:
        {chr(10).join([f'  • {exchange}: {count} instruments' for exchange, count in exchange_counts.items()])}
        
        📑 Segment Distribution:
        {chr(10).join([f'  • {segment}: {count} instruments' for segment, count in segment_counts.items()])}
        """
        
        messages.success(request, success_message)
        
    except Exception as e:
        messages.error(request, f'Error synchronizing instruments: {str(e)}')
    
    return redirect('mstock_trade:home') 




# def live_sensex(request):
#     return render(request, 'mstock_trade/live_sensex.html')
from django.conf import settings
def live_sensex(request):
    # ws_port = getattr(settings, 'DAPHNE_PORT', 8001)  # Default to 8000
    ws_port = 8001
    return render(request, 'mstock_trade/live_sensex.html', {'ws_port': ws_port})


from django.http import JsonResponse
import requests
import time,os

@access_token_required
def execute_trade(request):
    API_KEY = os.getenv('MSTOCK_API_KEY', 'default_api_key')
    ACCESS_TOKEN = os.getenv('MSTOCK_ACCESS_TOKEN', 'default_access_token')
    HEADERS = {
        "X-Mirae-Version": "1",
        "Authorization": f"token {API_KEY}:{ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    symbol = "SENSEX2561080000CE"
    exchange = "BFO"
    qty = "20"
    buy_price = "200"
    sell_price = "204"
    product = "NRML"
    order_type = "LIMIT"
    validity = "DAY"
    ORDER_URL = "https://api.mstock.trade/openapi/typea/orders/regular"

    buy_payload = {
        "tradingsymbol": symbol,
        "exchange": exchange,
        "transaction_type": "BUY",
        "order_type": order_type,
        "quantity": qty,
        "price": buy_price,
        "product": product,
        "validity": validity
    }

    buy_resp = requests.post(ORDER_URL, headers=HEADERS, data=buy_payload).json()

    if buy_resp.get("status") == "success":
        time.sleep(1)
        sell_payload = {
            "tradingsymbol": symbol,
            "exchange": exchange,
            "transaction_type": "SELL",
            "order_type": order_type,
            "quantity": qty,
            "price": sell_price,
            "product": product,
            "validity": validity
        }

        sell_resp = requests.post(ORDER_URL, headers=HEADERS, data=sell_payload).json()

        return JsonResponse({
            "status": "success",
            "buy_order": buy_resp,
            "sell_order": sell_resp
        })

    return JsonResponse({
        "status": "error",
        "message": buy_resp.get("message", "Buy order failed.")
    })

import csv

from .models import Instrument


def parse_date(date_str):
    if not date_str:
        return None
    # Try to parse date in common formats, adjust as per your API
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def to_decimal(value):
    try:
        return float(value) if value else None
    except Exception:
        return None

def to_int(value):
    try:
        return int(value) if value else None
    except Exception:
        return None

def load_instruments(request):
    api_service = MStockAPIService()
    result = api_service.get_instrument_master()

    if result['status'] != 'success':
        messages.error(request, "Error on loading instruments")
        # handle error as before
        return redirect('mstock_trade:dashboard')

    instruments_data = result['data']

    for row in instruments_data:
        # Update or create instrument by instrument_token
        Instrument.objects.update_or_create(
            instrument_token=row['instrument_token'],
            defaults={
                'exchange_token': row['exchange_token'],
                'trading_symbol': row['tradingsymbol'],
                'name': row['name'],
                'last_price': to_decimal(row.get('last_price')),
                'expiry': parse_date(row.get('expiry')),
                'strike': to_decimal(row.get('strike')),
                'tick_size': to_decimal(row.get('tick_size')),
                'lot_size': to_int(row.get('lot_size')),
                'instrument_type': row['instrument_type'],
                'segment': row['segment'],
                'exchange': row['exchange'],
            }
        )
    return redirect('mstock_trade:instrument_list')

# def load_instruments(request):
#     with open('data/instrument.csv', newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         instruments = []
#         for row in reader:
#             instruments.append(Instrument(
#                 instrument_token=row['instrument_token'],
#                 exchange_token=row['exchange_token'],
#                 trading_symbol=row['tradingsymbol'],
#                 name=row['name'],
#                 last_price=row.get('last_price') or None,
#                 expiry=row.get('expiry') or None,
#                 strike=row.get('strike') or None,
#                 tick_size=row.get('tick_size') or None,
#                 lot_size=row.get('lot_size') or None,
#                 instrument_type=row['instrument_type'],
#                 segment=row['segment'],
#                 exchange=row['exchange'],
#             ))
#         Instrument.objects.bulk_create(instruments, batch_size=1000)  # Efficient bulk insert[5]
#     return redirect('instrument_list')

# def load_instruments(request):
#     # existing_tokens = set(Instrument.objects.values_list('instrument_token', flat=True))
#     # instruments = []

#     api_service = MStockAPIService()
#     result = api_service.get_instrument_master()
#     if result['status'] != 'success':
#         # Handle error, e.g., show a message or redirect with error
#         # For now, just print or log and redirect
#         print(result.get('message', 'Unknown error'))
#         return redirect('instrument_list')

#     instruments_data = result['data']

#     existing_tokens = set(Instrument.objects.values_list('instrument_token', flat=True))
#     instruments = []
#     seen_tokens = set()
#     for row in instruments_data:
#         token = row['instrument_token']
#         if token in existing_tokens or token in seen_tokens:
#             continue  # Skip duplicates
#         seen_tokens.add(token)
#         instruments.append(Instrument(
#             instrument_token=token,
#             exchange_token=row['exchange_token'],
#             trading_symbol=row['tradingsymbol'],
#             name=row['name'],
#             last_price=row.get('last_price') or None,
#             expiry=row.get('expiry') or None,
#             strike=row.get('strike') or None,
#             tick_size=row.get('tick_size') or None,
#             lot_size=row.get('lot_size') or None,
#             instrument_type=row['instrument_type'],
#             segment=row['segment'],
#             exchange=row['exchange'],
#         ))
#     Instrument.objects.bulk_create(instruments, batch_size=1000)
#     return redirect('mstock_trade:instrument_list')

    
    # seen_tokens = set()
    # with open('data/instrument.csv', newline='', encoding='utf-8') as csvfile:
    #     reader = csv.DictReader(csvfile)
    #     for row in reader:
    #         token = row['instrument_token']
    #         if token in existing_tokens or token in seen_tokens:
    #             continue  # Skip duplicates
    #         seen_tokens.add(token)
    #         instruments.append(Instrument(
    #             instrument_token=token,
    #             exchange_token=row['exchange_token'],
    #             trading_symbol=row['tradingsymbol'],
    #             name=row['name'],
    #             last_price=row.get('last_price') or None,
    #             expiry=row.get('expiry') or None,
    #             strike=row.get('strike') or None,
    #             tick_size=row.get('tick_size') or None,
    #             lot_size=row.get('lot_size') or None,
    #             instrument_type=row['instrument_type'],
    #             segment=row['segment'],
    #             exchange=row['exchange'],
    #         ))
    # Instrument.objects.bulk_create(instruments, batch_size=1000)
    # return redirect('instrument_list')

from django.core.paginator import Paginator
from django.db.models import Q
def instrument_list(request):
    qs = Instrument.objects.all()

    # Filtering
    exchange = request.GET.get('exchange')
    if exchange:
        qs = qs.filter(exchange=exchange)
    segment = request.GET.get('segment')
    if segment:
        qs = qs.filter(segment=segment)
    symbol = request.GET.get('symbol')
    if symbol:
        # qs = qs.filter(trading_symbol__icontains=symbol)
        qs = qs.filter(
            Q(trading_symbol__icontains=symbol) |
            Q(instrument_token__icontains=symbol) |
            Q(exchange_token__icontains=symbol)
        )

    lot_size = request.GET.get('lot_size')
    if lot_size:
        qs = qs.filter(lot_size__icontains=lot_size)
    option_type = request.GET.get('option_type')
    if option_type:
        qs = qs.filter(instrument_type=option_type)

    instrument_type = request.GET.get('instrument_type')
    if instrument_type:
        qs = qs.filter(instrument_type__icontains=instrument_type)

    last_price = request.GET.get('last_price')
    if last_price:
        qs = qs.filter(last_price__icontains=last_price)


    # Sorting
    sort_by = request.GET.get('sort', 'trading_symbol')
    order = request.GET.get('order', 'asc')
    if order == 'desc':
        sort_by = '-' + sort_by
    qs = qs.order_by(sort_by)

    # For dropdowns: get unique exchanges and segments
    exchanges = Instrument.objects.order_by('exchange').values_list('exchange', flat=True).distinct()
    segments = Instrument.objects.order_by('segment').values_list('segment', flat=True).distinct()
    instrument_types = Instrument.objects.order_by('instrument_type').values_list('instrument_type', flat=True).distinct()

    # Define columns for display and sorting
    columns = [
        ('instrument_token', 'Instrument Token'),
        ('exchange_token', 'Exchange Token'),
        ('trading_symbol', 'Trading Symbol'),
        ('name', 'Name'),
        ('last_price', 'Last Price'),
        ('expiry', 'Expiry'),
        ('strike', 'Strike'),
        ('tick_size', 'Tick Size'),
        ('lot_size', 'Lot Size'),
        ('instrument_type', 'Instrument Type'),
        ('segment', 'Segment'),
        ('exchange', 'Exchange'),
    ]

    # Pagination
    paginator = Paginator(qs, 200)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total = qs.count()
    return render(request, 'mstock_trade/instruments.html', {
        'page_obj': page_obj,
        'exchanges': exchanges,
        'segments': segments,
        'columns': columns,
        'instrument_types': instrument_types,
        'total':total
    })

    # qs = Instrument.objects.all()

    # # Filtering
    # exchange = request.GET.get('exchange')
    # if exchange:
    #     qs = qs.filter(exchange=exchange)
    # segment = request.GET.get('segment')
    # if segment:
    #     qs = qs.filter(segment=segment)
    # symbol = request.GET.get('symbol')
    # if symbol:
    #     qs = qs.filter(trading_symbol__icontains=symbol)

    # # Sorting
    # sort_by = request.GET.get('sort', 'trading_symbol')
    # order = request.GET.get('order', 'asc')
    # if order == 'desc':
    #     sort_by = '-' + sort_by
    # qs = qs.order_by(sort_by)

    # # For dropdowns: get unique exchanges and segments
    # exchanges = Instrument.objects.order_by('exchange').values_list('exchange', flat=True).distinct()
    # segments = Instrument.objects.order_by('segment').values_list('segment', flat=True).distinct()

    # # Pagination
    # from django.core.paginator import Paginator
    # paginator = Paginator(qs, 50)
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)

    # return render(request, 'mstock_trade/instruments.html', {
    #     'page_obj': page_obj,
    #     'exchanges': exchanges,
    #     'segments': segments,
    # })

    # # Pagination for large datasets[6]
    # paginator = Paginator(qs, 50)  # 50 per page
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)

    # return render(request, 'mstock_trade/instruments.html', {'page_obj': page_obj})

# @access_token_required
# def instrument_master_view(request):
#     # Path to your CSV file (adjust as needed)
#     data_file = os.path.join(settings.BASE_DIR, 'data', 'instrument.csv')
#     instruments = []
#     # breakpoint()
#     with open(data_file, newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             # Clean or convert fields as needed
#             instruments.append({
#                 'exchange': row.get('exchange', ''),
#                 'symbol': row.get('symbol', ''),
#                 'token': row.get('token', ''),
#                 'segment': row.get('segment', ''),
#                 'instrument_type': row.get('instrument_type', ''),
#                 'expiry': row.get('expiry', ''),
#                 'strike': row.get('strike', ''),
#                 'option_type': row.get('option_type', ''),
#                 # Add more fields as required
#             })
#     return render(request, 'mstock_trade/instrument_master.html', {'instruments': instruments})

def live_data(request):
    return render(request,'mstock_trade/live.html')
