from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from meetups.models import Meetup
from teams.models import Roles


class TestIntegrationMeetups:
    @pytest.mark.parametrize(
        'role, expected_status',
        [
            (Roles.manager, 201),
            (Roles.admin, 201),
            (Roles.member, 403),
        ],
    )
    def test_create_meetup_by_role(
            self,
            role,
            expected_status,
            profiles,
            team,
            create_membership,
            auth_client,
            team_meetups_url,
    ):
        user = profiles['owner']
        create_membership(user, role)
        starts_at = timezone.now() + timedelta(hours=1)
        ends_at = starts_at + timedelta(hours=1)
        api_client = auth_client(user)
        response = api_client.post(
            team_meetups_url,
            {
                'title': 'Team meeting',
                'description': 'Test meeting',
                'starts_at': starts_at.isoformat(),
                'ends_at': ends_at.isoformat(),
                'participants': [],
            },
            format='json',
        )
        assert response.status_code == expected_status
        assert Meetup.objects.count() == (1 if expected_status == 201 else 0)

    def test_create_meetup_with_invalid_time_returns_400(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            team_meetups_url,
    ):
        manager = profiles['owner']
        create_membership(manager, Roles.manager)
        starts_at = timezone.now() + timedelta(hours=2)
        ends_at = starts_at - timedelta(hours=1)
        api_client = auth_client(manager)
        response = api_client.post(
            team_meetups_url,
            {
                'title': 'Invalid meeting',
                'description': 'Test meeting',
                'starts_at': starts_at.isoformat(),
                'ends_at': ends_at.isoformat(),
                'participants': [],
            },
            format='json',
        )
        assert response.status_code == 400
        assert Meetup.objects.count() == 0

    def test_create_meetup_with_participant_from_another_team_returns_400(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            team_meetups_url,
    ):
        manager = profiles['owner']
        outsider = profiles['outsider']
        create_membership(manager, Roles.manager)
        starts_at = timezone.now() + timedelta(hours=1)
        ends_at = starts_at + timedelta(hours=1)
        api_client = auth_client(manager)
        response = api_client.post(
            team_meetups_url,
            {
                'title': 'Team meeting',
                'description': 'Test meeting',
                'starts_at': starts_at.isoformat(),
                'ends_at': ends_at.isoformat(),
                'participants': [outsider.pk],
            },
            format='json',
        )
        assert response.status_code == 400
        assert Meetup.objects.count() == 0

    @pytest.mark.parametrize(
        'action, user_key',
        [
            ('list', 'member'),
            ('list', 'outsider'),
            ('retrieve', 'member'),
            ('retrieve', 'outsider'),
        ],
    )
    def test_meetup_access_for_member_and_outsider(
            self,
            action,
            user_key,
            profiles,
            create_membership,
            auth_client,
            team,
            meetup,
            team_meetups_url,
    ):
        create_membership(profiles['owner'], Roles.manager)
        create_membership(profiles['member'], Roles.member)
        api_client = auth_client(profiles[user_key])
        url = (
            team_meetups_url
            if action == 'list'
            else reverse(
                'team-meetups-detail',
                kwargs={'team_pk': team.pk, 'pk': meetup.pk},
            )
        )
        response = api_client.get(url)
        expected_status = 200 if user_key == 'member' else 403
        assert response.status_code == expected_status
        if response.status_code == 200 and action == 'list':
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['title'] == 'Existing meeting'
        if response.status_code == 200 and action == 'retrieve':
            assert response.data['title'] == 'Existing meeting'

    @pytest.mark.parametrize(
        'user_key, expected_status',
        [
            ('owner', 200),
            ('member', 403),
        ],
    )
    def test_update_meetup_permissions(
            self,
            user_key,
            expected_status,
            profiles,
            create_membership,
            auth_client,
            team,
            meetup,
    ):
        create_membership(profiles['owner'], Roles.manager)
        create_membership(profiles['member'], Roles.member)
        url = reverse(
            'team-meetups-detail',
            kwargs={
                'team_pk': team.pk,
                'pk': meetup.pk,
            },
        )
        api_client = auth_client(profiles[user_key])
        response = api_client.patch(
            url,
            {'title': 'Updated meeting'},
            format='json',
        )
        assert response.status_code == expected_status
        meetup.refresh_from_db()
        if expected_status == 200:
            assert meetup.title == 'Updated meeting'
        else:
            assert meetup.title == 'Existing meeting'

    @pytest.mark.parametrize(
        'user_key, expected_status',
        [
            ('owner', 204),
            ('member', 403),
        ],
    )
    def test_delete_meetup_permissions(
            self,
            user_key,
            expected_status,
            profiles,
            create_membership,
            auth_client,
            team,
            meetup,
    ):
        create_membership(profiles['owner'], Roles.manager)
        create_membership(profiles['member'], Roles.member)
        url = reverse(
            'team-meetups-detail',
            kwargs={
                'team_pk': team.pk,
                'pk': meetup.pk,
            },
        )
        api_client = auth_client(profiles[user_key])
        response = api_client.delete(url)
        assert response.status_code == expected_status
        assert Meetup.objects.filter(pk=meetup.pk).exists() == (expected_status != 204)
