
# mysite/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from cards import consumers 

from django.urls import re_path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")


import cards.routing
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                re_path(r"^ws/cards/(?P<room_name>[^/]+)/$", consumers.GameConsumer.as_asgi()),
            ])
        )
    ),

})
# application = ProtocolTypeRouter(
#     {
#         "http": django_asgi_app,
#         "websocket": AllowedHostsOriginValidator(
#             AuthMiddlewareStack(URLRouter(cards.routing.websocket_urlpatterns))
#         ),
#     }
# )

