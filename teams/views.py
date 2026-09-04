from django.db import transaction
from django.db.models.functions import uuid
from django.urls import reverse
from django.views.generic import RedirectView
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from teams.models import Team, Membership, Roles
from teams.permissions import MembershipPerms, TeamPerms
from teams.serializers import TeamShortSerializer, TeamSerializer, JoinTeamSerializer, MembershipSerializer, \
    MembershipRoleChangeSerializer, TeamUpdateSerializer


# Create your views here.


class TeamViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        if self.action in ('list', 'retrieve', 'update', 'partial_update', 'regen_invite_code'):
            return Team.objects.filter(profiles=self.request.user.profile)
        return Team.objects.none()

    def get_permissions(self):
        return [TeamPerms()]

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return TeamShortSerializer
        elif self.action in ['retrieve', 'regen_invite_code']:
            if self.action == 'retrieve':
                membership = Membership.objects.get(
                    team_id=self.kwargs['pk'],
                    profile=self.request.user.profile,
                )
                # Приглашать могут только эти роли
                if membership.role in (
                        Roles.manager,
                        Roles.admin,
                        Roles.owner,
                ):
                    return TeamSerializer
                return TeamShortSerializer
            else:
                return TeamSerializer
        elif self.action == 'partial_update':
            return TeamUpdateSerializer
        elif self.action == 'join':
            return JoinTeamSerializer
        else:
            return TeamShortSerializer

    @action(detail=True, methods=['post'], url_name='join')
    def join(self, request, *args, **kwargs):
        team = get_object_or_404(
            Team,
            pk=self.kwargs['pk'],
        )
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
        # Атомарность не нужна т.к создаём только membership
        membership = Membership.objects.create(team=team, profile=profile, role=Roles.member)
        return Response(self.get_serializer(team).data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        profile = self.request.user.profile
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save()
        Membership.objects.create(team=team, profile=profile, role=Roles.owner)
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_name='change_invite_code', url_path='invite_code')
    def regen_invite_code(self, request, *args, **kwargs):
        team = self.get_object()
        team.invite_code = uuid.UUID4()
        team.save(update_fields=['invite_code'])
        return Response(self.get_serializer(team).data, status=status.HTTP_200_OK)


class TeamTaskCommentsRedirectView(RedirectView):
    permanent = False  # 302

    def get_redirect_url(self, *args, **kwargs):
        task_id = kwargs['task_id']
        team_id = kwargs['team_id']
        base_url = reverse('task-comments-list', kwargs={'task_pk': task_id})
        #return f'{base_url}?team_pk={team_id}'
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

    # def get_object(self):
    #    team_id = self.kwargs.get('team_pk')
    #    profile_id = self.kwargs.get('profile_id')
    #    return self.get_queryset().get(team_id=team_id, profile_id=profile_id)
