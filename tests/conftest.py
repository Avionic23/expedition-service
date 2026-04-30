import pytest
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from expeditions.models import Expedition, ExpeditionMember
from authentication.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def chief(db):
    return User.objects.create_user(
        email='chief@test.com',
        name='Chief User',
        password='testpass123',
        role=User.Role.CHIEF,
    )


@pytest.fixture
def member1(db):
    return User.objects.create_user(
        email='member1@test.com',
        name='Member One',
        password='testpass123',
        role=User.Role.MEMBER,
    )


@pytest.fixture
def member2(db):
    return User.objects.create_user(
        email='member2@test.com',
        name='Member Two',
        password='testpass123',
        role=User.Role.MEMBER,
    )


@pytest.fixture
def member3(db):
    return User.objects.create_user(
        email='member3@test.com',
        name='Member Three',
        password='testpass123',
        role=User.Role.MEMBER,
    )


@pytest.fixture
def chief_client(chief):
    client = APIClient()
    client.force_authenticate(user=chief)
    return client


@pytest.fixture
def member1_client(member1):
    client = APIClient()
    client.force_authenticate(user=member1)
    return client


@pytest.fixture
def member2_client(member2):
    client = APIClient()
    client.force_authenticate(user=member2)
    return client


@pytest.fixture
def expedition(db, chief):
    return Expedition.objects.create(
        title='Test Expedition',
        description='Test description',
        start_at=timezone.now() - timedelta(hours=1),
        capacity=10,
        chief=chief,
    )


@pytest.fixture
def ready_expedition(expedition, chief_client, member1, member2):
    """Expedition in ready state with 2 confirmed members."""
    ExpeditionMember.objects.create(expedition=expedition, user=member1, state=ExpeditionMember.State.CONFIRMED)
    ExpeditionMember.objects.create(expedition=expedition, user=member2, state=ExpeditionMember.State.CONFIRMED)
    chief_client.post(f'/api/expeditions/{expedition.id}/status/', {'status': 'ready'})
    expedition.refresh_from_db()
    return expedition


@pytest.fixture
def active_expedition(ready_expedition, chief_client):
    """Expedition in active state."""
    chief_client.post(f'/api/expeditions/{ready_expedition.id}/status/', {'status': 'active'})
    ready_expedition.refresh_from_db()
    return ready_expedition
