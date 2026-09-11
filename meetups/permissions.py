from rest_framework.permissions import BasePermission

from teams.models import Membership, Roles


class MeetupPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        team_id = view.kwargs.get('team_pk')

        if team_id is None:
            return False

        membership = Membership.objects.filter(
            team_id=team_id,
            profile=request.user.profile,
        ).first()

        if membership is None:
            return False

        if view.action == 'create':
            return membership.role in (Roles.manager, Roles.admin)
        return True

    def has_object_permission(self, request, view, obj):
        is_member = Membership.objects.filter(
            team=obj.team,
            profile=request.user.profile,
        ).exists()

        if not is_member:
            return False

        if view.action == 'retrieve':
            return True

        if view.action in ('update', 'partial_update', 'destroy'):
            return obj.organizer == request.user.profile

        return False
