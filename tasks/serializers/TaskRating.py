from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from profiles.serializers.Profile import ProfileSerializer
from tasks.models import TaskRating
from tasks.serializers import TaskShortSerializer, TaskSerializer


class TaskRatingSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = TaskRating
        fields = ('task', 'author', 'score', 'score_comment', 'created_at')


class TaskRatingShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskRating
        fields = '__all__'


class TaskRatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskRating
        fields = ('score', 'score_comment')

    def validate(self, attrs):
        task = self.context['view'].get_task()
        author = self.context['request'].user.profile
        if self.context['view'].action == 'create':
            if TaskRating.objects.filter(
                    task=task,
                    author=author,
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже оценивали эту задачу.'
                )

        return attrs
