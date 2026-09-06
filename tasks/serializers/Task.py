from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer
from tasks.models import Task, TaskStatus
from teams.models import Membership, Roles, Team
from teams.serializers import Teams
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


class TaskShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ('description',)


class TaskCreateSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = get_object_or_404(
            Team,
            pk=self.context['view'].kwargs['team_pk'],
        )

        self.fields['assignee'].queryset = (
            Profile.objects
            .filter(memberships__team=team)
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
        team_id = self.context['view'].kwargs['team_pk']
        assignee = attrs['assignee']
        if not Membership.objects.filter(team_id=team_id, profile=assignee, ).exists():
            raise serializers.ValidationError(
                {'assignee': 'Нельзя назначить человека, который не состоит в данной команде.'}
            )
        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    # Указываем, что для записи assignee мы ждем ID (первичный ключ) профиля
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=False,  # Делаем необязательным для PATCH-запросов
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            team = self.instance.team
            self.fields['assignee'].queryset = (
                Profile.objects.filter(memberships__team=team)
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

    def validate_status(self, value):
        # если она Done - то она Done, не нравится - создавай новую задачу на исправление этой
        if self.instance.status == TaskStatus.DONE and value != TaskStatus.DONE:
            raise serializers.ValidationError(
                'Нельзя изменить статус завершённой задачи.'
            )

        return value

    def validate(self, attrs):
        request = self.context.get('request')
        task = self.instance

        membership = Membership.objects.get(profile=request.user.profile, team=task.team)

        if membership.role == Roles.member and task.created_by != request.user.profile:
            if set(attrs) != {'status'}:
                raise serializers.ValidationError('Участник может изменить только статус выполнения задачи')
        assignee = attrs.get('assignee')
        if assignee is not None:
            if not Membership.objects.filter(team=task.team, profile=assignee, ).exists():
                raise serializers.ValidationError(
                    {
                        'assignee': 'Нельзя назначить человека, который не состоит в данной команде.'
                    }
                )
        return attrs
