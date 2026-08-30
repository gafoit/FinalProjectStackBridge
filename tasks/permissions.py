from rest_framework.permissions import BasePermission

from teams.models import Membership, Roles


class TaskPermissions(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if view.action == 'create':
            team_id = view.kwargs.get('team_pk')
            return Membership.objects.filter(team_id=team_id, profile=request.user.profile,
                                             role__in=[Roles.owner, Roles.admin, Roles.manager]).exists()
        return True

    def has_object_permission(self, request, view, obj):
        membership = Membership.objects.filter(team=obj.team, profile=request.user.profile).first()
        if membership is None:
            return False

        if view.action == 'retrieve':
            return True

        if view.action == 'destroy':
            return membership.role in [Roles.admin, Roles.owner]

        if view.action in ('update', 'partial_update'):
            if membership.role in [Roles.admin, Roles.owner]:
                return True

            if obj.created_by == request.user.profile:
                return True

            return membership.role == Roles.member
        return False
