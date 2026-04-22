from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Expedition, ExpeditionMember


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'password', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ExpeditionMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    class Meta:
        model = ExpeditionMember
        fields = ['id', 'user', 'user_id', 'state', 'invited_at', 'confirmed_at']
        read_only_fields = ['id', 'state', 'invited_at', 'confirmed_at']


class ExpeditionSerializer(serializers.ModelSerializer):
    chief = UserSerializer(read_only=True)
    members = ExpeditionMemberSerializer(many=True, read_only=True)
    confirmed_members_count = serializers.SerializerMethodField()

    class Meta:
        model = Expedition
        fields = [
            'id', 'title', 'description', 'status', 'start_at', 'end_at',
            'capacity', 'chief', 'members', 'confirmed_members_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'chief', 'created_at', 'updated_at']

    def get_confirmed_members_count(self, obj):
        return obj.get_confirmed_members_count()


class ExpeditionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expedition
        fields = ['id', 'title', 'description', 'start_at', 'end_at', 'capacity']
        read_only_fields = ['id']


class ExpeditionStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Expedition.Status.choices)

    def validate_status(self, value):
        expedition = self.context.get('expedition')
        if not expedition.can_transition_to(value):
            raise serializers.ValidationError(
                f"Cannot transition from '{expedition.status}' to '{value}'"
            )
        return value


class InviteMemberSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate_user_id(self, user):
        if user.role != User.Role.MEMBER:
            raise serializers.ValidationError('Can only invite users with role "member"')

        expedition = self.context.get('expedition')
        if ExpeditionMember.objects.filter(expedition=expedition, user=user).exists():
            raise serializers.ValidationError('User is already invited to this expedition')

        return user