from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from meetups.models import Meetup
from meetups.permissions import MeetupPermission
from meetups.serializers.Meetup import MeetupShortSerializer, MeetupSerializer, MeetupCreateSerializer, \
    MeetupUpdateSerializer
from teams.models import Team


def validate_meeting_availability(
        *,
        organizer,
        participants,
        starts_at,
        ends_at,
        exclude_meetup=None,
):
    participants = list(participants)
    profiles = participants + [organizer]

    overlapping_meetups = Meetup.objects.filter(
        is_cancelled=False,
        starts_at__lte=ends_at,
        ends_at__gte=starts_at,
    ).filter(
        Q(organizer__in=profiles) |
        Q(participants__in=profiles)
    ).distinct()

    if exclude_meetup is not None:
        overlapping_meetups = overlapping_meetups.exclude(
            pk=exclude_meetup.pk,
        )

    if not overlapping_meetups.exists():
        return

    profile_ids = {profile.id for profile in profiles}

    busy_organizer_ids = set(
        overlapping_meetups
        .filter(organizer_id__in=profile_ids)
        .values_list('organizer_id', flat=True)
    )

    busy_participant_ids = set(
        overlapping_meetups
        .filter(participants__id__in=profile_ids)
        .values_list('participants__id', flat=True)
    )

    busy_ids = busy_organizer_ids | busy_participant_ids

    error = {}

    if organizer.id in busy_ids:
        error['organizer'] = 'Организатор уже занят в это время.'

    busy_participants = [
        {
            'id': participant.id,
            'username': participant.user.username,
        }
        for participant in participants
        if participant.id in busy_ids
    ]

    if busy_participants:
        error['participants'] = busy_participants

    raise ValidationError(error)


class MeetupViewSet(viewsets.ModelViewSet):
    permission_classes = [MeetupPermission]

    def get_team(self):
        return get_object_or_404(
            Team,
            pk=self.kwargs['team_pk'],
        )

    def get_queryset(self):
        queryset = Meetup.objects.all()

        team_id = self.kwargs.get('team_pk')
        if team_id is None:
            team_id = self.request.GET.get('team')
        queryset = queryset.filter(team__memberships__profile=self.request.user.profile)
        if team_id is not None:
            queryset = queryset.filter(team_id=team_id)
        # Чтобы можно было отделить встречи на которых я орг и я участник
        participating = self.request.GET.get('participating')
        organizing = self.request.GET.get('organizing')

        if participating == 'me':
            queryset = queryset.filter(
                participants=self.request.user.profile
            )

        if organizing == 'me':
            queryset = queryset.filter(
                organizer=self.request.user.profile
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return MeetupShortSerializer
        elif self.action == 'retrieve':
            return MeetupSerializer
        elif self.action == 'create':
            return MeetupCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MeetupUpdateSerializer
        else:
            return MeetupShortSerializer

    def perform_create(self, serializer):
        team = self.get_team()
        organizer = self.request.user.profile
        participants = serializer.validated_data['participants']

        validate_meeting_availability(
            organizer=organizer,
            participants=participants,
            starts_at=serializer.validated_data['starts_at'],
            ends_at=serializer.validated_data['ends_at'],
        )

        serializer.save(
            organizer=organizer,
            team=team,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        validated_data = serializer.validated_data

        organizer = instance.organizer
        participants = validated_data.get(
            'participants',
            instance.participants.all(),
        )
        starts_at = validated_data.get(
            'starts_at',
            instance.starts_at,
        )
        ends_at = validated_data.get(
            'ends_at',
            instance.ends_at,
        )

        validate_meeting_availability(
            organizer=organizer,
            participants=participants,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_meetup=instance,
        )

        serializer.save()

