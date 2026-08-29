from rest_framework import serializers

from profiles.serializers.Profile import ProfileSerializer
from tasks.models import Task, TaskStatus


class TaskSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=TaskStatus.choices)
    created_by = ProfileSerializer(read_only=True)
    assignee = ProfileSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ('title', 'description', 'created_by', 'assignee', 'due_date', 'status')


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'title',
            'description',
            'assignee',
            'due_date',
        )


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=TaskStatus.choices)

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save(update_fields=('status',))

    class Meta:
        model = Task
        fields = ('role',)
