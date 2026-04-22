from django.urls import path
from .consumers import ExpeditionConsumer

websocket_urlpatterns = [
    path('ws/expeditions/', ExpeditionConsumer.as_asgi()),
]