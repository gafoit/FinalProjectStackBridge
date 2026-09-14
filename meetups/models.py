from django.db import models

from profiles.models import Profile
from teams.models import Team


class Meetup(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='meetings',
        verbose_name='Команда',
    )
    organizer = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='organized_meetings',
        verbose_name='Организатор',
    )
    participants = models.ManyToManyField(
        Profile,
        related_name='meetings',
        verbose_name='Участники',
    )

    title = models.CharField(max_length=255, verbose_name='Тема')
    description = models.TextField(blank=True, verbose_name='Описание')

    starts_at = models.DateTimeField(verbose_name='Начало')
    ends_at = models.DateTimeField(verbose_name='Окончание')

    is_cancelled = models.BooleanField(default=False, verbose_name='Отменена')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')

    class Meta:
        verbose_name = 'Встреча'
        verbose_name_plural = 'Встречи'
        ordering = ['-starts_at']
