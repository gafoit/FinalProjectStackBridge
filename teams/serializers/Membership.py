from rest_framework import serializers

from profiles.serializers.Profile import ProfileSerializer
from teams.models import Membership, Roles
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
