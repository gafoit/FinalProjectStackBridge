from rest_framework import serializers

from profiles.serializers.Profile import ProfileSerializer
from teams.models import Team


class TeamShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'owner', 'name')
        extra_kwargs = {
            'owner': {'read_only': True}
        }


class TeamCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    def validate_name(self, name):
        if name == "":
            raise serializers.ValidationError("Name cannot be empty")
        return name

    class Meta:
        model = Team
        fields = ('name',)


class TeamSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer()

    class Meta:
        model = Team
        fields = ('id', 'owner', 'name', 'invite_code')

        extra_kwargs = {
            'owner': {'read_only': True},
            'name': {'read_only': True},
            'invite_code': {'read_only': True}
        }


class TeamUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)

    def validate_name(self, name):
        if name == "":
            raise serializers.ValidationError("Name cannot be empty")
        return name

    class Meta:
        model = Team
        fields = ('name',)


class JoinTeamSerializer(serializers.Serializer):
    invite_code = serializers.UUIDField()
