from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class WebSocketEventService:
    """Service to broadcast WebSocket events to expedition participants."""

    EVENT_MEMBER_INVITED = 'member_invited'
    EVENT_MEMBER_CONFIRMED = 'member_confirmed'
    EVENT_EXPEDITION_STATUS = 'expedition_status'
    EVENT_EXPEDITION_JOIN = 'expedition_join'

    @staticmethod
    def get_expedition_group_name(expedition_id):
        return f'expedition_{expedition_id}'

    @staticmethod
    def get_user_group_name(user_id):
        return f'user_{user_id}'

    @classmethod
    def broadcast_to_expedition(cls, expedition_id, event_type, data):
        """Broadcast an event to all users connected to an expedition."""
        channel_layer = get_channel_layer()
        group_name = cls.get_expedition_group_name(expedition_id)

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'expedition_event',
                'event_type': event_type,
                'data': data,
            }
        )

    @classmethod
    def broadcast_to_user(cls, user_id, event_type, data):
        channel_layer = get_channel_layer()
        group_name = cls.get_user_group_name(user_id)

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'expedition_event',
                'event_type': event_type,
                'data': data
            }
        )

    @classmethod
    def notify_member_invited(cls, expedition, member):
        """Notify when a member is invited to an expedition."""
        cls.broadcast_to_expedition(
            expedition.id,
            cls.EVENT_MEMBER_INVITED,
            {
                'expedition_id': expedition.id,
                'member': {
                    'id': member.id,
                    'user_id': member.user.id,
                    'email': member.user.email,
                    'name': member.user.name,
                    'state': member.state,
                    'invited_at': member.invited_at.isoformat(),
                }
            }
        )

    @classmethod
    def notify_member_confirmed(cls, expedition, member):
        """Notify when a member confirms participation."""
        cls.broadcast_to_expedition(
            expedition.id,
            cls.EVENT_MEMBER_CONFIRMED,
            {
                'expedition_id': expedition.id,
                'member': {
                    'id': member.id,
                    'user_id': member.user.id,
                    'email': member.user.email,
                    'name': member.user.name,
                    'state': member.state,
                    'confirmed_at': member.confirmed_at.isoformat() if member.confirmed_at else None,
                }
            }
        )

    @classmethod
    def notify_status_changed(cls, expedition):
        """Notify when expedition status changes."""
        cls.broadcast_to_expedition(
            expedition.id,
            cls.EVENT_EXPEDITION_STATUS,
            {
                'expedition_id': expedition.id,
                'status': expedition.status,
                'updated_at': expedition.updated_at.isoformat(),
            }
        )

    @classmethod
    def notify_joined_expedition(cls, expedition, user):
        """Notify when expedition created/joined for subscription"""
        cls.broadcast_to_user(
            user.id,
            cls.EVENT_EXPEDITION_JOIN,
            {
                'expedition_id': expedition.id,
            }
        )