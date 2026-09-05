from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import uuid
from rest_framework.reverse import reverse
from django.views.generic import RedirectView
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from teams.models import Team, Membership, Roles
from teams.permissions import MembershipPerms, TeamPerms
from teams.serializers import TeamShortSerializer, TeamSerializer, JoinTeamSerializer, MembershipSerializer, \
    MembershipRoleChangeSerializer, TeamUpdateSerializer, MembershipTransferOwnershipSerializer, TeamCreateSerializer


# Create your views here.


class TeamViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        qs = Team.objects.all()
        if self.action != 'join':
            qs = qs.filter(profiles=self.request.user.profile)
        return qs

    def get_permissions(self):
        return [TeamPerms()]

    def get_serializer_class(self):
        if self.action == 'list':
            return TeamShortSerializer
        elif self.action in 'create':
            return TeamCreateSerializer
        elif self.action in ['retrieve', 'regen_invite_code']:
            if self.action == 'retrieve':
                membership = Membership.objects.get(
                    team_id=self.kwargs['pk'],
                    profile=self.request.user.profile,
                )
                # Приглашать могут только эти роли
                if (
                        membership.role in (Roles.manager, Roles.admin)
                        or membership.team.owner == self.request.user.profile
                ):
                    return TeamSerializer
                return TeamShortSerializer
            else:
                return TeamSerializer
        elif self.action in ['partial_update', 'update']:
            return TeamUpdateSerializer
        elif self.action == 'join':
            return JoinTeamSerializer
        elif self.action == 'transfer_ownership':
            return MembershipTransferOwnershipSerializer
        else:
            return TeamShortSerializer

    @action(detail=True, methods=['post'], url_name='join')
    def join(self, request, *args, **kwargs):
        team = self.get_object()
        profile = self.request.user.profile
        serializer = JoinTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite_code = serializer.validated_data['invite_code']
        if invite_code != team.invite_code:
            raise serializers.ValidationError({
                'invite_code': 'Неверный код приглашения'
            })
        # Если уже в команде
        if Membership.objects.filter(team=team, profile=profile).exists():
            raise serializers.ValidationError(
                'Пользователь уже состоит в команде'
            )
        # Атомарность не обязательна так как создаём только membership
        membership = Membership.objects.create(team=team, profile=profile, role=Roles.member)
        # Редирект для красоты и удобства работы
        url = reverse(
            'team-members-detail',
            kwargs={
                'team_pk': team.pk,
                'profile_id': membership.profile_id,
            },
            request=request,
        )

        return Response(
            status=status.HTTP_303_SEE_OTHER,
            headers={'Location': url},
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        profile = self.request.user.profile
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save(owner=profile)
        Membership.objects.create(team=team, profile=profile, role=Roles.admin)
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_name='change_invite_code', url_path='invite_code')
    def regen_invite_code(self, request, *args, **kwargs):
        team = self.get_object()
        team.invite_code = uuid.UUID4()
        team.save(update_fields=['invite_code'])
        return Response(self.get_serializer(team).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_name='transfer_ownership', url_path='transfer_ownership')
    @transaction.atomic
    def transfer_ownership(self, request, *args, **kwargs):
        team = self.get_object()
        serializer = self.get_serializer()
        serializer.is_valid(raise_exception=True)
        team.owner = serializer.validated_data['profile']
        team.save(update_fields=['owner'])
        return Response(TeamSerializer(team).data)


class TeamTaskCommentsRedirectView(RedirectView):
    permanent = False  # 302

    def get_redirect_url(self, *args, **kwargs):
        task_id = kwargs['task_id']
        base_url = reverse('task-comments-list', kwargs={'task_pk': task_id})
        # return f'{base_url}?team_pk={team_id}'
        return f'{base_url}'


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    lookup_field = 'profile_id'
    http_method_names = ['get', 'patch', 'delete']

    def get_queryset(self):
        team_id = self.kwargs.get('team_pk')
        return Membership.objects.filter(team_id=team_id)

    def get_permissions(self):
        return [MembershipPerms()]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return MembershipRoleChangeSerializer
        return super().get_serializer_class()

    @transaction.atomic
    def perform_destroy(self, instance):
        team = instance.team
        if instance.profile != team.owner:
            instance.delete()
            return

        # Ищем нового по всем юзерам, неважно с какой ролью. У команды ДОЛЖЕН быть владелец
        new_owner = (
            Membership.objects
            .filter(team=team)
            .exclude(pk=instance.pk)
            .annotate(
                role_priority=Case(
                    When(role=Roles.admin, then=Value(3)),
                    When(role=Roles.manager, then=Value(2)),
                    When(role=Roles.member, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by('-role_priority', 'id')
            .first()
        )

        if new_owner is None:
            team.delete()
            return

        team.owner = new_owner.profile
        team.save(update_fields=['owner'])
        instance.delete()
