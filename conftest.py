from datetime import timedelta

from django.utils import timezone

import pytest
from django.urls import reverse

from meetups.models import Meetup
from profiles.models import Profile
from django.contrib.auth.models import User
from pytest_django.fixtures import db
from rest_framework.test import APIClient

from tasks.models import Task
from teams.models import Team, Membership, Roles


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def auth_client(client):
    def factory(profile):
        client.force_authenticate(user=profile.user)
        return client

    return factory

@pytest.fixture
def create_profile(db):
    def factory(username):
        # password не даём потому что так дольше работает
        return User.objects.create_user(
                username=username,
            ).profile

    return factory

# чтобы все были
@pytest.fixture
def profiles(create_profile):
    return {
        username: create_profile(username)
        for username in (
            'owner',
            'admin',
            'manager',
            'member',
            'outsider',
        )
    }


@pytest.fixture
def team(profiles):
    return Team.objects.create(
        name='Test Team',
        owner=profiles['owner'],
    )

@pytest.fixture
def other_team(profiles):
    return Team.objects.create(
        name='Other Team',
        owner=profiles['outsider'],
    )

@pytest.fixture
def create_membership(db, team):
    def factory(profile, role):
        return Membership.objects.create(
            team=team,
            profile=profile,
            role=role,
        )

    return factory

@pytest.fixture
def task(team, profiles)->Task:
    return Task.objects.create(
        title='Test task',
        description='Test description',
        team=team,
        created_by=profiles['owner'],
        assignee=profiles['member'],
        due_date=timezone.now() + timedelta(days=1),
    )


@pytest.fixture
def global_tasks_url():
    return reverse('tasks-list')


@pytest.fixture
def team_tasks_url(team):
    return reverse(
        'team-tasks-list',
        kwargs={'team_pk': team.pk},
    )


@pytest.fixture
def team_task_url(team, task):
    return reverse(
        'team-tasks-detail',
        kwargs={
            'team_pk': team.pk,
            'pk': task.pk,
        },
    )


@pytest.fixture
def global_task_url(task):
    return reverse(
        'tasks-detail',
        kwargs={'pk': task.pk},
    )

@pytest.fixture
def meetup(team, profiles):
    starts_at = timezone.now()

    return Meetup.objects.create(
        team=team,
        organizer=profiles['owner'],
        title='Existing meeting',
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
    )

@pytest.fixture
def team_meetups_url(team):
    return reverse(
        'team-meetups-list',
        kwargs={'team_pk': team.pk},
    )

