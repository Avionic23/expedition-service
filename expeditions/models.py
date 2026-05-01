from django.db import models
from django.utils import timezone
from authentication.models import User

class Expedition(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        READY = 'ready', 'Ready'
        ACTIVE = 'active', 'Active'
        FINISHED = 'finished', 'Finished'

    ALLOWED_TRANSITIONS = {
        'draft': ['ready'],
        'ready': ['active'],
        'active': ['finished'],
        'finished': [],
    }

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField()
    chief = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_expeditions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expeditions'

    def __str__(self):
        return self.title

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def get_confirmed_members_count(self):
        # return ExpeditionMember.objects.filter(expedition=self, state=ExpeditionMember.State.CONFIRMED).count()
        return self.members.filter(state=ExpeditionMember.State.CONFIRMED).count()

    def validate_activation(self):
        """Validate all conditions before activating expedition."""
        errors = []
        now = timezone.now()

        if self.start_at > now:
            errors.append(f'start_at must be <= now (start_at: {self.start_at}, now: {now})')

        confirmed_count = self.get_confirmed_members_count()
        if confirmed_count < 2:
            errors.append(f'At least 2 confirmed members required (current: {confirmed_count})')

        if confirmed_count > self.capacity:
            errors.append(f'Confirmed members ({confirmed_count}) exceed capacity ({self.capacity})')

        confirmed_members = self.members.filter(state=ExpeditionMember.State.CONFIRMED)
        for member in confirmed_members:
            active_expeditions = ExpeditionMember.objects.filter(
                user=member.user,
                state=ExpeditionMember.State.CONFIRMED,
                expedition__status=Expedition.Status.ACTIVE
            ).exclude(expedition=self)
            if active_expeditions.exists():
                errors.append(f'Member {member.user.email} is already in another active expedition')

        return errors


class ExpeditionMember(models.Model):
    class State(models.TextChoices):
        INVITED = 'invited', 'Invited'
        CONFIRMED = 'confirmed', 'Confirmed'

    id = models.BigAutoField(primary_key=True)
    expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expedition_memberships')
    state = models.CharField(max_length=10, choices=State.choices, default=State.INVITED)
    invited_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'expedition_members'
        unique_together = ['expedition', 'user']

    def __str__(self):
        return f'{self.user.email} - {self.expedition.title}'