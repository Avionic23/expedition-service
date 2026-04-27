from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

from expeditions.models import User

class Session(models.Model):
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_sessions')
    device_id = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sessions'

    def __str__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + settings.SESSION_DB_TTL
        super().save(*args, **kwargs)