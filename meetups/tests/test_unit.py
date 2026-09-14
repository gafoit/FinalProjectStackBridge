from datetime import timedelta

import pytest
from rest_framework.exceptions import ValidationError

from meetups.views import validate_meeting_availability
from teams.models import Roles


class TestUnitMeetups:
    def test_overlapping_meeting_for_participant_raises_error(
            self,
            profiles,
            team,
            create_membership,
            meetup,
    ):
        participant = profiles['member']

        create_membership(profiles['owner'], Roles.admin)
        create_membership(participant, Roles.member)
        meetup.participants.add(participant)

        new_starts_at = meetup.starts_at + timedelta(minutes=30)
        new_ends_at = meetup.ends_at + timedelta(minutes=30)

        with pytest.raises(ValidationError) as exc_info:
            validate_meeting_availability(
                organizer=profiles['owner'],
                participants=[participant],
                starts_at=new_starts_at,
                ends_at=new_ends_at,
            )

        error = exc_info.value.detail

        assert 'participants' in error
        assert int(error['participants'][0]['id']) == participant.id
        assert str(error['participants'][0]['username']) == (
            participant.user.username
        )

    def test_overlapping_meeting_for_organizer_raises_error(
            self,
            profiles,
            team,
            create_membership,
            meetup,
    ):
        create_membership(profiles['owner'], Roles.admin)

        new_starts_at = meetup.starts_at + timedelta(minutes=30)
        new_ends_at = meetup.ends_at + timedelta(minutes=30)

        with pytest.raises(ValidationError) as exc_info:
            validate_meeting_availability(
                organizer=profiles['owner'],
                participants=[],
                starts_at=new_starts_at,
                ends_at=new_ends_at,
            )

        error = exc_info.value.detail

        assert 'organizer' in error
        assert str(error['organizer']) == 'Организатор уже занят в это время.'

    def test_updating_meeting_does_not_conflict_with_itself(
            self,
            profiles,
            team,
            create_membership,
            meetup,
    ):
        create_membership(profiles['owner'], Roles.admin)

        validate_meeting_availability(
            organizer=profiles['owner'],
            participants=[],
            starts_at=meetup.starts_at,
            ends_at=meetup.ends_at,
            exclude_meetup=meetup,
        )
