from django.db import models
from django.db.models.functions import uuid

from profiles.models import Profile


# Create your models here.

class Roles(models.TextChoices):
    member = 'member', 'Участник'
    manager = 'manager', 'Менеджер'
    admin = 'admin', 'Администратор'


role_priority = {
    Roles.member: 1,
    Roles.manager: 2,
    Roles.admin: 3,
}


class Team(models.Model):
    name = models.CharField(max_length=100)
    invite_code = models.UUIDField(default=uuid.UUID4, editable=False, unique=True)
    # Это стоило сделать сразу, но почему бы не на 6 миграцию
    owner = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='owned_teams',
    )

    def __str__(self):
        return self.name


class Membership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='memberships')
    role = models.TextField(max_length=7, choices=Roles.choices, default=Roles.member)

    def __str__(self):
        return f'{self.team.name}[{self.profile.username}: {self.role}]'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('team', 'profile'),
                name='unique_team_profile',
            ),
        ]
