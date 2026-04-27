from rest_framework import viewsets, status, permissions
from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from .serializers import SessionCreateSerializer, SessionSerializer, SessionInvalidateSerializer
from .models import Session

class SessionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = SessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = Session.objects.create(
            user=serializer.validated_data['user'],
            device_id=serializer.validated_data['device_id'],
        )

        cache.set(f'session_{session.uuid}', session.user.id, timeout=settings.SESSION_REDIS_TTL)

        return Response(SessionSerializer(session).data, status=201)

    @action(detail=False, methods=['post'], url_path='invalidate')
    def invalidate(self, request):
        serializer = SessionInvalidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uuid = serializer.validated_data['uuid']
        count = Session.objects.filter(uuid=uuid).update(active=False)
        if count > 0:
            cache.delete(f'session_{uuid}')

        return Response(status=status.HTTP_204_NO_CONTENT)