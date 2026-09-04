from textwrap import shorten

from rest_framework import serializers

from profiles.serializers.Profile import ProfileSerializer
from tasks.models import TaskComment


class TaskCommentSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ('id', 'author', 'text', 'created_at')


class TaskCommentShortSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return shorten(obj.text, width=150, break_long_words=False, placeholder='')

    class Meta:
        model = TaskComment
        fields = ('author', 'text', 'created_at')
