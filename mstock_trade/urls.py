from django.urls import path
from . import views

app_name = 'mstock_trade'
from django.urls import re_path
from . import consumers

# websocket_urlpatterns = [
#     re_path(r'ws/sensex/$', consumers.SensexConsumer.as_asgi()),
# ]
urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.mstock_login, name='login'),
    path('verify-otp/', views.mstock_verify_otp, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('market/quotes/', views.market_quote, name='market_quote'),
    path('market/quotes/ajax/', views.market_quote_ajax, name='market_quote_ajax'),
    path('market/instruments/', views.instrument_search, name='instrument_search'),
    path('option-chain/', views.option_chain, name='option_chain'),
    path('intraday-chart/', views.intraday_chart, name='intraday_chart'),
    path('gainers-losers/', views.gainers_losers, name='gainers_losers'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-book/', views.order_book, name='order_book'),
    path('trade-history/', views.trade_history, name='trade_history'),
    path('position-list/', views.position_list, name='position_list'),
    path('convert-position/', views.convert_position, name='convert_position'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('fund-summary/', views.fund_summary_view, name='fund_summary'),
    path('create-strategy/', views.create_strategy, name='create_strategy'),
    path('execute-trade/', views.execute_trade, name='execute_trade'),
    path('cancel-all-orders/', views.cancel_all_orders, name='cancel_all_orders'),
    path('access-info/', views.access_info, name='access_info'),
    path('sync-instruments/', views.sync_instruments, name='sync_instruments'),



    path('live-sensex/', views.live_sensex, name='live_sensex'),
    # path('execute-quick-trade/', views.execute_quick_trade, name='execute_quick_trade'),
    # path('instrument-master/', views.instrument_master_view, name='instrument_master'),
    path('load-instruments/', views.load_instruments, name='load_instruments'),
    path('instruments/', views.instrument_list, name='instrument_list'),
    path("live-data/", views.live_data, name='live_data'),

] 