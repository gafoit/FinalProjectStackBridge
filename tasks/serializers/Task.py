from rest_framework import serializers

from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer
from tasks.models import Task, TaskStatus
from teams.models import Membership, Roles
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

    def validate(self, attrs):
        if not Membership.objects.filter(profile=attrs.get("assignee"), team=self.context['view'].kwargs['team_pk']).exists():
            raise serializers.ValidationError('Нельзя назначить человека который не состоит в данной команде')
        return attrs


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

        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
            'assignee': {'required': False},
            'due_date': {'required': False},
        }

    def validate(self, attrs):
        request = self.context.get('request')
        task = self.instance

        membership = Membership.objects.get(profile=request.user.profile, team=task.team)

        if membership.role == Roles.member and task.created_by != request.user.profile:
            if set(attrs) != {'status'}:
                raise serializers.ValidationError('Участник может изменить только статус выполнения задачи')
        return attrs
