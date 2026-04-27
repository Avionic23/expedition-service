from rest_framework import serializers
from expeditions.models import User
from .models import Session

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