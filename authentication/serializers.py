from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Session, User

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


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['uuid']

class SessionCreateSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField()

    def validate_user_credentials(self, email, password):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid Credentials')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid Credentials')

        return user

    def validate(self, attrs):
        user = self.validate_user_credentials(attrs['email'], attrs['password'])
        attrs['user'] = user
        return attrs

class SessionInvalidateSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()