import uuid

import pytest
from django.urls import reverse

from teams.models import Team, Roles, Membership


class TestTeams:
    def team_url(self, team):
        return reverse(
            'teams-detail',
            kwargs={'pk': team.pk},
        )

    def invite_code_url(self, team):
        return reverse(
            'teams-change_invite_code',
            kwargs={'pk': team.pk},
        )

    def join_url(self, team):
        return reverse(
            'teams-join',
            kwargs={'pk': team.pk},
        )

    def transfer_ownership_url(self, team):
        return reverse(
            'teams-transfer_ownership',
            kwargs={'pk': team.pk},
        )

    def test_create_team(self, auth_client, profiles):
        api_client = auth_client(profiles['owner'])
        response = api_client.post(
            reverse('teams-list'),
            {'name': 'New Team'},
            format='json'
        )

        assert response.status_code == 201
        assert Team.objects.get(pk=response.json()['id']).name == 'New Team'

    @pytest.mark.parametrize(
        'username, role',
        [
            ('owner', Roles.admin),
            ('admin', Roles.admin),
            ('manager', Roles.manager),
            ('member', Roles.member),
        ]
    )
    def test_list_returns_only_users_teams(self, profiles, team,
                                           other_team, create_membership,
                                           auth_client, username,
                                           role):
        profile = profiles[username]
        create_membership(profile, role)
        api_client = auth_client(profile)
        response = api_client.get(reverse('teams-list'))
        team_ids = [item['id'] for item in response.json()['results']]
        assert response.status_code == 200
        assert team.id in team_ids
        assert not other_team in team_ids

    @pytest.mark.parametrize(
        'username,role,expected_status_code,sees_invite_code',
        [
            pytest.param('owner', Roles.admin, 200, True),
            pytest.param('admin', Roles.admin, 200, True),
            pytest.param('manager', Roles.manager, 200, True),
            pytest.param('member', Roles.member, 200, False),
            pytest.param('outsider', None, 404, False),

        ]
    )
    def test_retrieve_team_results(self, profiles, team, create_membership, auth_client, username, role,
                                   expected_status_code, sees_invite_code):
        profile = profiles[username]
        if role is not None:
            create_membership(profile, role)
        api_client = auth_client(profile)
        response = api_client.get(self.team_url(team))
        # проверяем и доступ к инфе команды, и то что в ней видно
        assert response.status_code == expected_status_code
        if response.status_code == 200:
            assert response.json()['id'] == team.id
            assert ('invite_code' in response.json()) == sees_invite_code

    @pytest.mark.parametrize(
        'username,role,expected_status_code',
        [
            pytest.param('owner', Roles.admin, 200),
            pytest.param('admin', Roles.admin, 200),
            pytest.param('manager', Roles.manager, 403),
            pytest.param('member', Roles.member, 403),
            pytest.param('outsider', None, 404),
        ]
    )
    def test_update_team(self, profiles, team, create_membership, auth_client, username, role, expected_status_code):
        profile = profiles[username]
        if role:
            create_membership(profile, role)
        api_client = auth_client(profile)
        old_name = team.name
        response = api_client.patch(self.team_url(team), {'name': 'Updated Team'})
        # Проверяем что запрос прошел
        assert response.status_code == expected_status_code
        team.refresh_from_db()
        # И что имя действительно изменено
        if expected_status_code == 200:
            assert team.name == 'Updated Team'
        else:
            assert team.name == old_name

    @pytest.mark.parametrize(
        'username,role,expected_status_code',
        [
            pytest.param('owner', Roles.admin, 204),
            pytest.param('admin', Roles.admin, 403),
            # Это даже проверять не стоит, но типа ладно
            pytest.param('manager', Roles.manager, 403),
            pytest.param('member', Roles.member, 403),
            pytest.param('outsider', None, 404),
        ]
    )
    def test_delete_team(self, profiles, team, create_membership, auth_client, username, role, expected_status_code):
        profile = profiles[username]
        if role:
            create_membership(profile, role)
        api_client = auth_client(profile)
        team_pk = team.pk
        response = api_client.delete(self.team_url(team))
        assert response.status_code == expected_status_code
        if expected_status_code == 204:
            assert not Team.objects.filter(pk=team_pk).exists()
        else:
            assert Team.objects.filter(pk=team_pk).exists()

    @pytest.mark.parametrize(
        'username,role,expected_status_code',
        [
            pytest.param('owner', Roles.admin, 200),
            pytest.param('admin', Roles.admin, 200),
            pytest.param('manager', Roles.manager, 403),
            # Тут только он вообще не должен это знать уметь видеть. Но тоже проверили
            pytest.param('member', Roles.member, 403),
            pytest.param('outsider', None, 404),
        ]
    )
    def test_can_regen_invite_code(self, profiles, team, create_membership, auth_client, username, role,
                                   expected_status_code):
        profile = profiles[username]
        if role:
            create_membership(profile, role)
        api_client = auth_client(profile)
        old_code = team.invite_code
        response = api_client.post(self.invite_code_url(team))
        assert response.status_code == expected_status_code
        team.refresh_from_db()
        if expected_status_code == 200:
            assert team.invite_code != old_code
        else:
            assert team.invite_code == old_code

    def test_valid_join(self, profiles, team, auth_client):
        profile = profiles['member']
        api_client = auth_client(profile)
        response = api_client.post(
            self.join_url(team),
            {'invite_code': team.invite_code}
        )
        assert response.status_code == 303
        assert Membership.objects.filter(team=team, profile=profile).exists()

    def test_invalid_join(self, profiles, team, auth_client):
        profile = profiles['member']
        api_client = auth_client(profile)
        response = api_client.post(
            self.join_url(team),
            {'invite_code': uuid.uuid4()}
        )
        assert response.status_code == 400
        assert not Membership.objects.filter(team=team, profile=profile).exists()

    def test_multiple_join(self, profiles, team, auth_client):
        profile = profiles['member']
        api_client = auth_client(profile)
        response = api_client.post(
            self.join_url(team),
            {'invite_code': team.invite_code}
        )
        assert response.status_code == 303
        assert Membership.objects.filter(team=team, profile=profile).exists()
        second_response = api_client.post(
            self.join_url(team),
            {'invite_code': team.invite_code}
        )
        assert second_response.status_code == 400
        assert Membership.objects.filter(team=team, profile=profile).count() == 1

    @pytest.mark.parametrize(
        'username,role,expected_status_code',
        [
            pytest.param('owner', Roles.admin, 200),
            pytest.param('admin', Roles.admin, 404),
            pytest.param('manager', Roles.manager, 404),
        ]
    )
    def test_transfer_ownership(self,profiles, team, auth_client, create_membership, create_profile, username, role,
                                expected_status_code):
        profile = profiles[username]
        create_membership(team.owner, role)
        # fake_users
        fake_admin = create_profile('fake_admin')
        # Добавляем чтобы было кому передать управление
        create_membership(fake_admin, Roles.admin)
        old_owner = team.owner
        api_client = auth_client(profile)
        response = api_client.post(
            self.transfer_ownership_url(team),
            {'profile': fake_admin.pk}
        )
        assert response.status_code == expected_status_code

        team.refresh_from_db()

        if username == 'owner':
            assert team.owner == fake_admin
        else:
            assert team.owner == old_owner
