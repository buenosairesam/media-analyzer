"""
ASGI config for media_analyzer project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Set Django settings first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_analyzer.settings.development')

# Initialize Django ASGI application early to ensure the AppRegistry is populated
django_asgi_app = get_asgi_application()

# Now import channels and consumers after Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from streaming.consumers import StreamAnalysisConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/stream/", StreamAnalysisConsumer.as_asgi()),
        ])
    ),
})
