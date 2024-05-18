import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from .consumers import ChatConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"chat/(?P<room_name>[^/]+)/(?P<user>[^/]+)/$", ChatConsumer.as_asgi()),
        ])
    ),
})