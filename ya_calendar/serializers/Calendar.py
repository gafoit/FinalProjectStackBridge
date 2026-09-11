from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from meetups.models import Meetup
from tasks.models import Task


class CalendarQuerySerializer(serializers.Serializer):
    from_date = serializers.DateTimeField(
        source="from",
        required=False,
    )
    to_date = serializers.DateTimeField(
        source="to",
        required=False,
    )

    def validate(self, attrs):
        from_date = attrs.get("from")
        to_date = attrs.get("to")
        now = timezone.now()

        if from_date is None and to_date is None:
            # Текущая неделя: понедельник 00:00 -> следующий понедельник 00:00
            start_of_week = now - timedelta(days=now.weekday())
            from_date = start_of_week.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            to_date = from_date + timedelta(days=7)

        elif from_date is not None and to_date is None:
            to_date = now

        elif from_date is None and to_date is not None:
            from_date = now

        if from_date > to_date:
            raise serializers.ValidationError(
                "'from' must be earlier than or equal to 'to'."
            )

        attrs["from"] = from_date
        attrs["to"] = to_date

        return attrs


class CalendarTaskSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "type",
            "id",
            "title",
            "due_date",
            "status",
            "team",
        )

    def get_type(self, obj):
        return "task"

    def get_team(self, obj):
        return {
            "id": obj.team_id,
            "name": obj.team.name,
        }


class CalendarMeetupSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()

    class Meta:
        model = Meetup
        fields = (
            "type",
            "id",
            "title",
            "starts_at",
            "ends_at",
            "is_cancelled",
            "team",
        )

    def get_type(self, obj):
        return "meetup"

    def get_team(self, obj):
        return {
            "id": obj.team_id,
            "name": obj.team.name,
        }