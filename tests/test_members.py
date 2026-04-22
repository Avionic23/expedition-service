import pytest

from expeditions.models import Expedition, ExpeditionMember


@pytest.mark.django_db
class TestInviteMember:
    def url(self, expedition_id):
        return f'/api/expeditions/{expedition_id}/invite/'

    def test_chief_can_invite_member(self, chief_client, expedition, member1):
        response = chief_client.post(self.url(expedition.id), {'user_id': member1.id})
        assert response.status_code == 201
        assert response.data['state'] == 'invited'

    def test_cannot_invite_chief_role_user(self, chief_client, expedition, chief):
        other_chief = chief.__class__.objects.create_user(
            email='other_chief@test.com',
            name='Other Chief',
            password='testpass123',
            role='chief',
        )
        response = chief_client.post(self.url(expedition.id), {'user_id': other_chief.id})
        assert response.status_code == 400

    def test_cannot_invite_same_member_twice(self, chief_client, expedition, member1):
        chief_client.post(self.url(expedition.id), {'user_id': member1.id})
        response = chief_client.post(self.url(expedition.id), {'user_id': member1.id})
        assert response.status_code == 400

    def test_cannot_invite_to_active_expedition(self, chief_client, active_expedition, member3):
        response = chief_client.post(self.url(active_expedition.id), {'user_id': member3.id})
        assert response.status_code == 400

    def test_cannot_invite_to_finished_expedition(self, chief_client, active_expedition, member3, chief_client_post=None):
        active_expedition.status = Expedition.Status.FINISHED
        active_expedition.save()
        response = chief_client.post(self.url(active_expedition.id), {'user_id': member3.id})
        assert response.status_code == 400

    def test_non_chief_cannot_invite(self, member1_client, member1, expedition, member2):
        ExpeditionMember.objects.create(expedition=expedition, user=member1)
        response = member1_client.post(self.url(expedition.id), {'user_id': member2.id})
        assert response.status_code == 403

    def test_unrelated_user_gets_404(self, member1_client, expedition, member2):
        response = member1_client.post(self.url(expedition.id), {'user_id': member2.id})
        assert response.status_code == 404

    def test_unauthenticated_cannot_invite(self, api_client, expedition, member1):
        response = api_client.post(self.url(expedition.id), {'user_id': member1.id})
        assert response.status_code == 401


@pytest.mark.django_db
class TestConfirmParticipation:
    def url(self, expedition_id):
        return f'/api/expeditions/{expedition_id}/confirm/'

    def test_invited_member_can_confirm(self, member1_client, expedition, member1):
        ExpeditionMember.objects.create(expedition=expedition, user=member1)
        response = member1_client.post(self.url(expedition.id))
        assert response.status_code == 200
        assert response.data['state'] == 'confirmed'

    def test_non_invited_user_cannot_confirm(self, member2_client, expedition, member2):
        response = member2_client.post(self.url(expedition.id))
        assert response.status_code == 404

    def test_already_confirmed_member_cannot_confirm_again(self, member1_client, expedition, member1):
        ExpeditionMember.objects.create(
            expedition=expedition,
            user=member1,
            state=ExpeditionMember.State.CONFIRMED,
        )
        response = member1_client.post(self.url(expedition.id))
        assert response.status_code == 400

    def test_chief_cannot_confirm_on_behalf_of_member(self, chief_client, expedition, member1):
        ExpeditionMember.objects.create(expedition=expedition, user=member1)
        response = chief_client.post(self.url(expedition.id))
        assert response.status_code == 404

    def test_unauthenticated_cannot_confirm(self, api_client, expedition, member1):
        ExpeditionMember.objects.create(expedition=expedition, user=member1)
        response = api_client.post(self.url(expedition.id))
        assert response.status_code == 401
