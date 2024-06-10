import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from .consumers import ChatConsumer, BattleConsumer, RoomDeleteConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"chat/(?P<room_name>[^/]+)/(?P<user>[^/]+)/$", ChatConsumer.as_asgi()),
            re_path(r"chat-delete/(?P<room_name>[^/]+)/$", RoomDeleteConsumer.as_asgi()),
            re_path(r"battle/(?P<room_id>[^/]+)/(?P<user>[^/]+)/$", BattleConsumer.as_asgi()),
        ])
    ),
})