from django.core.cache import cache
from django.http import HttpRequest
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from config import settings
from .models import Session, User

class SessionAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        header = request.headers.get("Authorization")
        if not header:
            return None

        parts = header.split(' ')
        if len(parts) < 2:
            return None

        session_id = parts[1]
        user_id = cache.get(f'session_{session_id}')

        if user_id:
            return User.objects.get(id=user_id), None

        try:
            session = Session.objects.get(uuid=session_id, active=True, expires_at__gt=timezone.now())
        except Session.DoesNotExist:
            raise AuthenticationFailed('Invalid or expired session')

        session.expires_at = timezone.now() + settings.SESSION_DB_TTL
        session.save()
        cache.set(f'session_{session.uuid}', session.user.id, timeout=settings.SESSION_REDIS_TTL)

        return session.user, None