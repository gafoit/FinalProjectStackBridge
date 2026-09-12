from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from meetups.models import Meetup
from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer
from teams.models import Team
from teams.serializers import TeamShortSerializer


class MeetupShortSerializer(serializers.ModelSerializer):
    team = TeamShortSerializer(read_only=True)
    organizer = ProfileSerializer(read_only=True)

    class Meta:
        model = Meetup
        fields = ('id', 'team', 'organizer', 'title', 'starts_at', 'ends_at')


class MeetupSerializer(serializers.ModelSerializer):
    team = TeamShortSerializer(read_only=True)
    organizer = ProfileSerializer(read_only=True)
    participants = ProfileSerializer(read_only=True, many=True)

    class Meta:
        model = Meetup
        fields = (
            'id',
            'team',
            'organizer',
            'title',
            'description',
            'starts_at',
            'ends_at',
            'participants',
            'is_cancelled',
            'created_at',
            'updated_at',
        )


class MeetupCreateSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=True,
        many=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = get_object_or_404(
            Team,
            pk=self.context['view'].kwargs['team_pk'],
        )

        user_profile = self.context['request'].user.profile

        self.fields['participants'].child_relation.queryset = (
            Profile.objects
            .filter(memberships__team=team)
            .exclude(pk=user_profile.pk)
            .distinct()
        )


    class Meta:
        model = Meetup
        fields = ('title', 'description', 'starts_at', 'ends_at', 'participants')

    def validate(self, attrs):
        if attrs['starts_at'] >= attrs['ends_at']:
            raise serializers.ValidationError(
                {
                    "starts_at": 'Встреча не может начаться позже или одновременно с концом встречи',
                    "ends_at": 'Встреча не может закончится раньше или одновременно с началом встречи',
                }
            )
        participants = attrs['participants']
        if len(participants) != len(set(participants)):
            raise serializers.ValidationError(
                {"participants": "Участники не должны повторяться."}
            )
        if self.context['request'].user.profile in participants and len(participants) == 1:
            raise serializers.ValidationError(
                {'participants': 'Организатор уже является участником встречи, добавьте других участников'})
        return attrs


class MeetupUpdateSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=False,
        many=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            return
        team = self.instance.team

        user_profile = self.context['request'].user.profile

        self.fields['participants'].child_relation.queryset = (
            Profile.objects
            .filter(memberships__team=team)
            .exclude(pk=user_profile.pk)
            .distinct()
        )


    def validate(self, attrs):
        if self.instance.is_cancelled:
            if attrs.get('is_cancelled') is not False:
                raise serializers.ValidationError(
                    'Отменённую встречу можно только восстановить.'
                )

            if len(attrs) > 1:
                raise serializers.ValidationError(
                    'Отменённую встречу нельзя изменять.'
                )
        starts_at = attrs.get('starts_at', self.instance.starts_at)
        ends_at = attrs.get('ends_at', self.instance.ends_at)
        if starts_at >= ends_at:
            raise serializers.ValidationError(
                {
                    "starts_at": 'Встреча не может начаться позже или одновременно с концом встречи',
                    "ends_at": 'Встреча не может закончится раньше или одновременно с началом встречи',
                }
            )
        participants = attrs.get('participants')

        if participants is not None:
            if len(participants) != len(set(participants)):
                raise serializers.ValidationError(
                    {"participants": "Участники не должны повторяться."}
                )
        return attrs

    class Meta:
        model = Meetup
        fields = ('title', 'description', 'starts_at', 'ends_at', 'participants', 'is_cancelled')
