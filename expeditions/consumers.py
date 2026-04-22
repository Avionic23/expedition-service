import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q

from .models import Expedition
from .events import WebSocketEventService


class ExpeditionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for expedition real-time events."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        user_expeditions = await self.get_user_expedition_ids()
        self.groups = []

        user_group_name = WebSocketEventService.get_user_group_name(self.user.id)
        await self.channel_layer.group_add(user_group_name, self.channel_name)
        self.groups.append(user_group_name)

        for expedition_id in user_expeditions:
            group_name = WebSocketEventService.get_expedition_group_name(expedition_id)
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.groups.append(group_name)

        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to expedition events',
            'subscribed_expeditions': user_expeditions
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        for group_name in getattr(self, 'groups', []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'subscribe':
                expedition_id = data.get('expedition_id')
                await self.handle_subscribe(expedition_id)
            elif action == 'unsubscribe':
                expedition_id = data.get('expedition_id')
                await self.handle_unsubscribe(expedition_id)
            elif action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_subscribe(self, expedition_id):
        """Subscribe to a specific expedition's events."""
        if not expedition_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'expedition_id required'
            }))
            return

        has_access = await self.check_expedition_access(expedition_id)
        if not has_access:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Access denied to this expedition'
            }))
            return

        group_name = WebSocketEventService.get_expedition_group_name(expedition_id)
        if group_name not in self.groups:
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.groups.append(group_name)

        await self.send(text_data=json.dumps({
            'type': 'subscribed',
            'expedition_id': expedition_id
        }))

    async def handle_unsubscribe(self, expedition_id):
        """Unsubscribe from a specific expedition's events."""
        if not expedition_id:
            return

        group_name = WebSocketEventService.get_expedition_group_name(expedition_id)
        if group_name in self.groups:
            await self.channel_layer.group_discard(group_name, self.channel_name)
            self.groups.remove(group_name)

        await self.send(text_data=json.dumps({
            'type': 'unsubscribed',
            'expedition_id': expedition_id
        }))

    async def expedition_event(self, event):
        """Handle expedition events from channel layer."""
        if event['event_type'] == 'expedition_join':
            if event['data'].get('expedition_id') is None:
                return
            group_name = WebSocketEventService.get_expedition_group_name(event['data'].get('expedition_id'))
            if group_name not in self.groups:
                await self.channel_layer.group_add(group_name, self.channel_name)
                self.groups.append(group_name)
        else:
            await self.send(text_data=json.dumps({
                'type': event['event_type'],
                'data': event['data']
            }))

    @database_sync_to_async
    def get_user_expedition_ids(self):
        """Get IDs of expeditions where user is chief or member."""
        expeditions = Expedition.objects.filter(
            Q(chief=self.user) | Q(members__user=self.user)
        ).distinct().values_list('id', flat=True)
        return list(expeditions)

    @database_sync_to_async
    def check_expedition_access(self, expedition_id):
        """Check if user has access to the expedition."""
        return Expedition.objects.filter(
            Q(id=expedition_id) & (Q(chief=self.user) | Q(members__user=self.user))
        ).exists()