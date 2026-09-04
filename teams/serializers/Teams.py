from django.db.models.functions import uuid
from rest_framework import serializers

from profiles.serializers.Profile import ProfileSerializer
from teams.models import Team, Membership, Roles


class TeamShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name')


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name', 'invite_code')

        extra_kwargs = {
            'name': {'read_only': True},
            'invite_code': {'read_only': True}
        }


class TeamUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Team
        fields = ('name',)


class JoinTeamSerializer(serializers.Serializer):
    invite_code = serializers.UUIDField()
