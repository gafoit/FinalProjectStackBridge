from rest_framework import serializers

from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer
from tasks.models import Task, TaskStatus
from teams.models import Membership
from teams.serializers.Teams import TeamShortSerializer


class TaskSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)
    assignee = ProfileSerializer(read_only=True)
    team = TeamShortSerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'team',
            'created_by',
            'assignee',
            'due_date',
            'status',
        )
        read_only_fields = (
            'id',
            'title',
            'due_date',
            'status',
        )


class TaskCreateSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=True,
    )
    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'assignee',
            'due_date',
        )


class TaskUpdateSerializer(serializers.ModelSerializer):
    # Указываем, что для записи assignee мы ждем ID (первичный ключ) профиля
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=False,  # Делаем необязательным для PATCH-запросов
    )

    class Meta:
        model = Task
        # Указываем только те поля, которые разрешено обновлять
        fields = (
            'title',
            'description',
            'assignee',
            'due_date',
            'status',
        )
