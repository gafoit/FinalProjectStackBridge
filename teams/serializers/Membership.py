from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.relations import PrimaryKeyRelatedField

from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer
from teams.models import Membership, Roles, Team
from . import Teams
from .Teams import TeamShortSerializer


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
    # role = serializers.ChoiceField(
    #    choices=Roles.choices,
    # )

    def update(self, instance, validated_data):
        instance.role = validated_data['role']
        instance.save(update_fields=['role'])
        return instance

    def validate_role(self, value):
        if value in Roles.values:
            return value
        else:
            raise serializers.ValidationError('Такой роли не существует')

    class Meta:
        model = Membership
        fields = ('role',)


class MembershipTransferOwnershipSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = get_object_or_404(
            Team,
            pk=self.context['view'].kwargs['pk'],
        )

        self.fields['profile'].queryset = (
            Profile.objects
            .filter(memberships__team=team)
            .exclude(pk=team.owner_id)
        )

