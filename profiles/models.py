from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver


# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teams = models.ManyToManyField('teams.Team', through='teams.Membership', related_name='profiles')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        ordering = ['user__username']

    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return self.username
