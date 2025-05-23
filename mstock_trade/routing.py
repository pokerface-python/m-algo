# mainapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/stocks/$', consumers.StockConsumer.as_asgi()),
    # re_path(r'ws/timer/$', consumers.TimerConsumer.as_asgi()),
]


# # # trading_platform/routing.py
# # from channels.routing import ProtocolTypeRouter

# # application = ProtocolTypeRouter({
# #     # Empty for now (add WebSocket routing later)
# #     print("RⱤrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrewrewrfdadfuoigjhdfyiugvshaiydfhugjsv")
# # })

# from django.urls import re_path
# from . import consumers

# # websocket_urlpatterns = [
# #     re_path(r'ws/sensex/$', consumers.YourConsumer.as_asgi()),
# # ]
# websocket_urlpatterns = [
#     re_path(r'ws/sensex/$', consumers.SensexConsumer.as_asgi()),
# ]

