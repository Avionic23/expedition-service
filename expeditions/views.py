from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import Expedition, ExpeditionMember
from .serializers import (
    ExpeditionSerializer, ExpeditionCreateSerializer,
    ExpeditionStatusSerializer, InviteMemberSerializer,
    ExpeditionMemberSerializer
)
from .events import WebSocketEventService
from authentication.authentication import SessionAuthentication
from authentication.models import User


class IsChief(permissions.BasePermission):
    """Permission check for chief role."""

    def has_permission(self, request, view):
        return request.user.role == User.Role.CHIEF


class IsExpeditionChief(permissions.BasePermission):
    """Permission check for expedition chief."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Expedition):
            return obj.chief == request.user
        return False


class ExpeditionViewSet(viewsets.ModelViewSet):
    serializer_class = ExpeditionSerializer
    authentication_classes = [SessionAuthentication]

    def get_queryset(self):
        """Return expeditions where user is chief or member."""
        user = self.request.user
        return Expedition.objects.filter(
            Q(chief=user) | Q(members__user=user)
        ).distinct().prefetch_related('members', 'members__user')

    def get_serializer_class(self):
        if self.action == 'create':
            return ExpeditionCreateSerializer
        return ExpeditionSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated(), IsChief()]
        if self.action in ['update', 'partial_update', 'destroy', 'set_status', 'invite_member']:
            return [permissions.IsAuthenticated(), IsExpeditionChief()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create expedition (chief only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expedition = Expedition.objects.create(
            chief=request.user,
            **serializer.validated_data
        )

        WebSocketEventService.notify_joined_expedition(expedition, self.request.user)

        return Response(
            ExpeditionSerializer(expedition).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='status')
    def set_status(self, request, pk=None):
        """Change expedition status (chief only)."""
        expedition = self.get_object()

        serializer = ExpeditionStatusSerializer(
            data=request.data,
            context={'expedition': expedition}
        )
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        # Additional validation for activation
        if new_status == Expedition.Status.ACTIVE:
            errors = expedition.validate_activation()
            if errors:
                return Response(
                    {'errors': errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        expedition.status = new_status
        expedition.save()

        WebSocketEventService.notify_status_changed(expedition)

        return Response(ExpeditionSerializer(expedition).data)

    @action(detail=True, methods=['post'], url_path='invite')
    def invite_member(self, request, pk=None):
        """Invite a member to expedition (chief only)."""
        expedition = self.get_object()

        if expedition.status in [Expedition.Status.ACTIVE, Expedition.Status.FINISHED]:
            return Response(
                {'error': 'Cannot invite members to active or finished expedition'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InviteMemberSerializer(
            data=request.data,
            context={'expedition': expedition}
        )
        serializer.is_valid(raise_exception=True)

        member = ExpeditionMember.objects.create(
            expedition=expedition,
            user=serializer.validated_data['user_id']
        )

        WebSocketEventService.notify_joined_expedition(expedition, member.user)
        WebSocketEventService.notify_member_invited(expedition, member)

        return Response(
            ExpeditionMemberSerializer(member).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_participation(self, request, pk=None):
        """Confirm participation (invited member only)."""
        expedition = self.get_object()

        try:
            membership = ExpeditionMember.objects.get(
                expedition=expedition,
                user=request.user
            )
        except ExpeditionMember.DoesNotExist:
            return Response(
                {'error': 'You are not invited to this expedition'},
                status=status.HTTP_404_NOT_FOUND
            )

        if membership.state != ExpeditionMember.State.INVITED:
            return Response(
                {'error': 'Can only confirm from invited state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.state = ExpeditionMember.State.CONFIRMED
        membership.confirmed_at = timezone.now()
        membership.save()

        WebSocketEventService.notify_member_confirmed(expedition, membership)

        return Response(ExpeditionMemberSerializer(membership).data)

    @action(detail=True, methods=['get'], url_path='members')
    def list_members(self, request, pk=None):
        """List all members of an expedition."""
        expedition = self.get_object()
        members = expedition.members.all()
        serializer = ExpeditionMemberSerializer(members, many=True)
        return Response(serializer.data)