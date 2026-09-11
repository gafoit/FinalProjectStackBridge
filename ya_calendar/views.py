from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from meetups.models import Meetup
from tasks.models import Task
from ya_calendar.serializers.Calendar import CalendarQuerySerializer, CalendarMeetupSerializer, CalendarTaskSerializer


class CalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query_serializer = CalendarQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)

        from_date = query_serializer.validated_data["from"]
        to_date = query_serializer.validated_data["to"]

        profile = request.user.profile

        tasks = Task.objects.filter(
            assignee=profile,
            due_date__gte=from_date,
            due_date__lt=to_date,
        ).select_related("team")

        meetups = Meetup.objects.filter(
            Q(organizer=profile) |
            Q(participants=profile),
            starts_at__gte=from_date,
            starts_at__lt=to_date,
        ).select_related("team").distinct()

        events = [
            *CalendarTaskSerializer(tasks, many=True).data,
            *CalendarMeetupSerializer(meetups, many=True).data,
        ]

        events.sort(
            key=lambda event: (
                event.get("due_date") or event.get("starts_at")
            )
        )

        return Response(events)