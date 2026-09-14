from datetime import timedelta

from django.utils import timezone

import pytest

from tasks.models import TaskStatus, Task
from teams.models import Roles


class TestTasks:
    @pytest.mark.parametrize(
        'username, role',
        [
            pytest.param('owner', Roles.admin),
            pytest.param('admin', Roles.admin),
            pytest.param('manager', Roles.manager),
            pytest.param('member', Roles.member),
        ],
    )
    def test_list_tasks(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            global_tasks_url,
            task,
            username,
            role,
    ):
        create_membership(profiles[username], role)

        api_client = auth_client(profiles[username])
        response = api_client.get(global_tasks_url)

        assert response.status_code == 200
        assert len(response.json()['results']) == 1

    @pytest.mark.parametrize(
        'username, expected_status_code',
        [
            pytest.param('owner', 200),
            pytest.param('member', 200),
            pytest.param('outsider', 404),
        ],
    )
    def test_retrieve_task(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            global_task_url,
            task,
            username,
            expected_status_code,
    ):
        if username != 'outsider':
            role = Roles.admin if username == 'owner' else Roles.member
            create_membership(profiles[username], role)

        api_client = auth_client(profiles[username])
        response = api_client.get(global_task_url)

        assert response.status_code == expected_status_code

        if expected_status_code == 200:
            assert response.json()['title'] == 'Test task'

    def test_list_tasks_assigned_to_me(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            global_tasks_url,
            task,
    ):
        profile = profiles['owner']
        create_membership(profile, Roles.manager)

        api_client = auth_client(profile)

        response = api_client.get(
            global_tasks_url,
            {'assigned': 'me'},
        )

        assert response.status_code == 200
        assert len(response.json()['results']) == 0

        task.assignee = profile
        task.save()

        response = api_client.get(
            global_tasks_url,
            {'assigned': 'me'},
        )

        assert response.status_code == 200
        assert len(response.json()['results']) == 1

    def test_list_tasks_created_by_me(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            global_tasks_url,
            task,
    ):
        profile = profiles['owner']
        create_membership(profile, Roles.manager)

        api_client = auth_client(profile)
        response = api_client.get(
            global_tasks_url,
            {'created': 'me'},
        )

        assert response.status_code == 200
        assert len(response.json()['results']) == 1

    def test_list_tasks_by_team(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            global_tasks_url,
            task,
    ):
        profile = profiles['owner']
        create_membership(profile, Roles.manager)

        api_client = auth_client(profile)
        response = api_client.get(
            global_tasks_url,
            {'team': team.pk},
        )

        assert response.status_code == 200
        assert len(response.json()['results']) == 1

    def test_create_task(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            team_tasks_url,
    ):
        manager = profiles['owner']
        member = profiles['member']

        create_membership(manager, Roles.manager)
        create_membership(member, Roles.member)

        api_client = auth_client(manager)

        response = api_client.post(
            team_tasks_url,
            {
                'title': 'New task',
                'description': 'New description',
                'assignee': member.pk,
                'due_date': (
                        timezone.now() + timedelta(days=2)
                ).isoformat(),
                'status': TaskStatus.OPEN,
            },
            format='json',
        )

        assert response.status_code == 201
        assert Task.objects.filter(title='New task').exists()

    @pytest.mark.parametrize(
        'username, role, expected_status_code',
        [
            pytest.param('owner', Roles.admin, 200),
            pytest.param('member', Roles.member, 400),
        ],
    )
    def test_update_task(
            self,
            profiles,
            team,
            create_membership,
            auth_client,
            team_task_url,
            task,
            username,
            role,
            expected_status_code,
    ):
        profile = profiles[username]
        create_membership(profile, role)

        api_client = auth_client(profile)
        response = api_client.patch(
            team_task_url,
            {'title': 'Updated task'},
            format='json',
        )

        assert response.status_code == expected_status_code

        if expected_status_code == 200:
            task.refresh_from_db()
            assert task.title == 'Updated task'

    def test_outsider_cannot_see_task(
            self,
            profiles,
            auth_client,
            global_task_url,
            task,
    ):
        api_client = auth_client(profiles['outsider'])

        response = api_client.get(global_task_url)

        assert response.status_code == 404

    def test_unauthenticated_cannot_list_tasks(
            self,
            client,
            global_tasks_url,
    ):
        response = client.get(global_tasks_url)

        assert response.status_code == 401