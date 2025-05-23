import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algo_trading.settings')


import django
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import mstock_trade.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(
        mstock_trade.routing.websocket_urlpatterns))
})
# get

# """
# ASGI config for algo_trading project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
# """

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algo_trading.settings')

# application = get_asgi_application()

# import os
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application
# import mstock_trade.routing

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algo_trading.settings')

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             mstock_trade.routing.websocket_urlpatterns
#         )
#     ),
# # })

# import os
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application
# import mstock_trade.routing

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algo_trading.settings')

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             mstock_trade.routing.websocket_urlpatterns
#         )
#     ),
# })
