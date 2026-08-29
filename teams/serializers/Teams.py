from random import choices

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


class JoinTeamSerializer(serializers.Serializer):
    invite_code = serializers.UUIDField()


class NewMembershipSerializer(serializers.Serializer):
    team = TeamShortSerializer()
    profile = ProfileSerializer()
    role = serializers.CharField(read_only=True)

    class Meta:
        model = Membership
        fields = ('team', 'profile', 'role')


class MembershipSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = Membership
        fields = ('profile', 'role')


class MembershipRoleChangeSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=Roles.choices,
    )

    def update(self, instance, validated_data):
        instance.role = validated_data['role']
        instance.save(update_fields=['role'])
        return instance

    class Meta:
        model = Membership
        fields = ('role',)
