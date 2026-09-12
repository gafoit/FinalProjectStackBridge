from django.db import models

from profiles.models import Profile
from teams.models import Team


class Meetup(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="meetings",
    )
    organizer = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name="organized_meetings",
    )
    participants = models.ManyToManyField(
        Profile,
        related_name="meetings",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    is_cancelled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-updated_at']
