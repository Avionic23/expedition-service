import pytest
from datetime import timedelta

from django.utils import timezone

from expeditions.models import Expedition, ExpeditionMember


@pytest.mark.django_db
class TestCreateExpedition:
    url = '/api/expeditions/'

    def test_chief_can_create(self, chief_client):
        response = chief_client.post(self.url, {
            'title': 'New Expedition',
            'start_at': timezone.now().isoformat(),
            'capacity': 5,
        })
        assert response.status_code == 201
        assert response.data['status'] == 'draft'

    def test_member_cannot_create(self, member1_client):
        response = member1_client.post(self.url, {
            'title': 'New Expedition',
            'start_at': timezone.now().isoformat(),
            'capacity': 5,
        })
        assert response.status_code == 403

    def test_unauthenticated_cannot_create(self, api_client):
        response = api_client.post(self.url, {
            'title': 'New Expedition',
            'start_at': timezone.now().isoformat(),
            'capacity': 5,
        })
        assert response.status_code == 401

    def test_status_defaults_to_draft(self, chief_client):
        response = chief_client.post(self.url, {
            'title': 'New Expedition',
            'start_at': timezone.now().isoformat(),
            'capacity': 5,
        })
        assert response.data['status'] == 'draft'


@pytest.mark.django_db
class TestListExpeditions:
    url = '/api/expeditions/'

    def test_chief_sees_own_expeditions(self, chief_client, expedition):
        response = chief_client.get(self.url)
        assert response.status_code == 200
        ids = [e['id'] for e in response.data]
        assert expedition.id in ids

    def test_member_sees_expeditions_they_belong_to(self, member1_client, expedition, member1):
        ExpeditionMember.objects.create(expedition=expedition, user=member1)
        response = member1_client.get(self.url)
        ids = [e['id'] for e in response.data]
        assert expedition.id in ids

    def test_member_cannot_see_unrelated_expeditions(self, member1_client, expedition):
        response = member1_client.get(self.url)
        ids = [e['id'] for e in response.data]
        assert expedition.id not in ids

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestStatusTransitions:
    def url(self, expedition_id):
        return f'/api/expeditions/{expedition_id}/status/'

    def test_draft_to_ready(self, chief_client, expedition):
        response = chief_client.post(self.url(expedition.id), {'status': 'ready'})
        assert response.status_code == 200
        assert response.data['status'] == 'ready'

    def test_ready_to_active(self, chief_client, ready_expedition):
        response = chief_client.post(self.url(ready_expedition.id), {'status': 'active'})
        assert response.status_code == 200
        assert response.data['status'] == 'active'

    def test_active_to_finished(self, chief_client, active_expedition):
        response = chief_client.post(self.url(active_expedition.id), {'status': 'finished'})
        assert response.status_code == 200
        assert response.data['status'] == 'finished'

    def test_draft_to_active_is_invalid(self, chief_client, expedition):
        response = chief_client.post(self.url(expedition.id), {'status': 'active'})
        assert response.status_code == 400

    def test_draft_to_finished_is_invalid(self, chief_client, expedition):
        response = chief_client.post(self.url(expedition.id), {'status': 'finished'})
        assert response.status_code == 400

    def test_finished_to_ready_is_invalid(self, chief_client, active_expedition):
        chief_client.post(self.url(active_expedition.id), {'status': 'finished'})
        response = chief_client.post(self.url(active_expedition.id), {'status': 'ready'})
        assert response.status_code == 400

    def test_member_cannot_change_status(self, member1_client, member1, expedition):
        ExpeditionMember.objects.create(expedition=expedition, user=member1)
        response = member1_client.post(self.url(expedition.id), {'status': 'ready'})
        assert response.status_code == 403

    def test_non_member_gets_404(self, member1_client, expedition):
        response = member1_client.post(self.url(expedition.id), {'status': 'ready'})
        assert response.status_code == 404


@pytest.mark.django_db
class TestActivationValidation:
    def url(self, expedition_id):
        return f'/api/expeditions/{expedition_id}/status/'

    def test_fails_when_start_at_in_future(self, chief_client, chief, member1, member2):
        expedition = Expedition.objects.create(
            title='Future Expedition',
            start_at=timezone.now() + timedelta(days=1),
            capacity=10,
            chief=chief,
        )
        ExpeditionMember.objects.create(expedition=expedition, user=member1, state=ExpeditionMember.State.CONFIRMED)
        ExpeditionMember.objects.create(expedition=expedition, user=member2, state=ExpeditionMember.State.CONFIRMED)
        expedition.status = Expedition.Status.READY
        expedition.save()

        response = chief_client.post(self.url(expedition.id), {'status': 'active'})
        assert response.status_code == 400

    def test_fails_when_fewer_than_2_confirmed_members(self, chief_client, chief, member1):
        expedition = Expedition.objects.create(
            title='Test',
            start_at=timezone.now() - timedelta(hours=1),
            capacity=10,
            chief=chief,
            status=Expedition.Status.READY,
        )
        ExpeditionMember.objects.create(expedition=expedition, user=member1, state=ExpeditionMember.State.CONFIRMED)

        response = chief_client.post(self.url(expedition.id), {'status': 'active'})
        assert response.status_code == 400

    def test_fails_when_confirmed_exceed_capacity(self, chief_client, chief, member1, member2):
        expedition = Expedition.objects.create(
            title='Test',
            start_at=timezone.now() - timedelta(hours=1),
            capacity=1,
            chief=chief,
            status=Expedition.Status.READY,
        )
        ExpeditionMember.objects.create(expedition=expedition, user=member1, state=ExpeditionMember.State.CONFIRMED)
        ExpeditionMember.objects.create(expedition=expedition, user=member2, state=ExpeditionMember.State.CONFIRMED)

        response = chief_client.post(self.url(expedition.id), {'status': 'active'})
        assert response.status_code == 400

    def test_fails_when_member_in_another_active_expedition(self, chief_client, chief, member1, member2, active_expedition):
        expedition = Expedition.objects.create(
            title='Second Expedition',
            start_at=timezone.now() - timedelta(hours=1),
            capacity=10,
            chief=chief,
            status=Expedition.Status.READY,
        )
        ExpeditionMember.objects.create(expedition=expedition, user=member1, state=ExpeditionMember.State.CONFIRMED)
        ExpeditionMember.objects.create(expedition=expedition, user=member2, state=ExpeditionMember.State.CONFIRMED)

        response = chief_client.post(self.url(expedition.id), {'status': 'active'})
        assert response.status_code == 400

    def test_succeeds_with_all_conditions_met(self, chief_client, ready_expedition):
        response = chief_client.post(self.url(ready_expedition.id), {'status': 'active'})
        assert response.status_code == 200
        assert response.data['status'] == 'active'
