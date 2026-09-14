import pytest
from django.urls import reverse

from teams.models import Roles, Membership, Team


class TestMembership:
    def members_url(self, team):
        return reverse(
            'team-members-list',
            kwargs={'team_pk': team.pk},
        )

    def member_url(self, team, profile):
        return reverse(
            'team-members-detail',
            kwargs={
                'team_pk': team.pk,
                'profile_id': profile.pk,
            },
        )

    @pytest.mark.parametrize(
        'username, expected_status_code',
        [
            pytest.param('owner', 200),
            pytest.param('admin', 200),
            pytest.param('manager', 200),
            pytest.param('member', 200),
            pytest.param('outsider', 403),
        ]
    )
    def test_list_members(self, profiles, team, create_membership, auth_client, username, expected_status_code):
        profile = profiles[username]
        for name, r in zip(['owner', 'admin', 'manager', 'member'],
                           [Roles.admin, Roles.admin, Roles.manager, Roles.member]):
            create_membership(profiles[name], r)
        api_client = auth_client(profile)
        response = api_client.get(self.members_url(team))
        assert response.status_code == expected_status_code
        if expected_status_code == 200:
            assert response.json()['count'] == 4

    @pytest.mark.parametrize(
        'actor, actor_role, target, target_role, new_role, expected_status_code',
        [
            # admin может менять роль member
            pytest.param('admin', Roles.admin, 'member', Roles.member, Roles.manager, 200),
            # manager может изменить member → member
            pytest.param('manager', Roles.manager, 'member', Roles.member, Roles.member, 200),
            # manager может повысить member → manager
            pytest.param('manager', Roles.manager, 'member', Roles.member, Roles.manager, 200),
            # manager не может менять admin
            pytest.param('manager', Roles.manager, 'admin', Roles.admin, Roles.member, 403),
            # member не может менять другого member
            pytest.param('member', Roles.member, 'outsider', Roles.member, Roles.admin, 403),
            # admin не может менять owner
            pytest.param('admin', Roles.admin, 'owner', Roles.admin, Roles.member, 403),
        ]
    )
    def test_role_change(self, profiles, team, create_membership, auth_client, actor, actor_role, target, target_role,
                         new_role, expected_status_code):
        act = profiles[actor]
        tar = profiles[target]
        create_membership(act, actor_role)
        create_membership(tar, target_role)

        api_client = auth_client(act)
        response = api_client.patch(self.member_url(team, tar), {'role': new_role})
        assert response.status_code == expected_status_code
        qs = Membership.objects.filter(team=team, profile=tar)
        assert qs.exists()
        if expected_status_code == 200:
            assert qs.get().role == new_role
        else:
            assert qs.get().role == target_role

    @pytest.mark.parametrize(
        'actor, actor_role, target, target_role, expected_status_code',
        [
            # member может выйти
            pytest.param('member', Roles.member, 'member', Roles.member, 204),
            # admin может удалить member
            pytest.param('admin', Roles.admin, 'member', Roles.member, 204),
            # admin НЕ может удалить owner
            pytest.param('admin', Roles.admin, 'owner', Roles.admin, 403),
            # manager не может удалить member
            pytest.param('manager', Roles.manager, 'member', Roles.member, 403),
            # member не может удалить другого member
            pytest.param('member', Roles.member, 'outsider', Roles.member, 403),
        ]
    )
    def test_delete_membership(self, profiles, team, create_membership, auth_client, actor, actor_role, target,
                               target_role, expected_status_code):

        act = profiles[actor]
        tar = profiles[target]
        create_membership(act, actor_role)
        if actor != target:
            create_membership(tar, target_role)

        api_client = auth_client(act)
        response = api_client.delete(self.member_url(team, tar))
        # print(response.status_code, response.json())
        assert response.status_code == expected_status_code

    def test_owner_leaving_transfers_ownership_to_highest_role(self, profiles, team, create_membership, auth_client):
        owner = profiles['owner']
        admin = profiles['admin']
        manager = profiles['manager']

        create_membership(owner, Roles.admin)
        create_membership(admin, Roles.admin)
        create_membership(manager, Roles.manager)

        api_client = auth_client(owner)
        response = api_client.delete(self.member_url(team, owner))

        assert response.status_code == 204

        team.refresh_from_db()

        assert team.owner == admin

    @pytest.mark.parametrize(
        'member_role',
        [
            Roles.admin,
            Roles.manager,
            Roles.member
        ],
    )
    def test_owner_leaving_transfers_ownership_to_remaining_member(self, profiles, team, create_membership, auth_client,
                                                                   member_role):
        owner = profiles['owner']
        member = profiles['member']

        create_membership(owner, Roles.admin)
        create_membership(member, member_role)

        api_client = auth_client(owner)
        response = api_client.delete(self.member_url(team, owner))

        assert response.status_code == 204

        team.refresh_from_db()

        assert team.owner == member

    def test_owner_leaving_deletes_team_if_no_members_left(
            self, profiles, team, create_membership, auth_client
    ):
        owner = profiles['owner']

        create_membership(owner, Roles.admin)

        api_client = auth_client(owner)
        response = api_client.delete(self.member_url(team, owner))

        assert response.status_code == 204

        assert not Team.objects.filter(pk=team.pk).exists()
