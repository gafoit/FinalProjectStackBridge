from rest_framework.permissions import BasePermission, SAFE_METHODS

from teams.models import Membership, Roles


class TaskPermissions(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if view.action == 'create':
            team_id = view.kwargs.get('team_pk')
            return Membership.objects.filter(team_id=team_id, profile=request.user.profile,
                                             role__in=[Roles.admin, Roles.manager]).exists()
        return True

    def has_object_permission(self, request, view, obj):
        membership = Membership.objects.filter(team=obj.team, profile=request.user.profile).first()
        if membership is None:
            return False

        if view.action == 'retrieve':
            return True

        if view.action == 'destroy':
            return membership.role == Roles.admin or obj.team.owner == request.user.profile

        if view.action in ('update', 'partial_update'):
            if membership.role == Roles.admin or obj.team.owner == request.user.profile:
                return True

            if obj.created_by == request.user.profile:
                return True
            if obj.assignee == request.user.profile:
                return True
            return membership.role == Roles.member
        return False


class TaskCommentPermissions(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        profile = request.user.profile

        membership = obj.task.team.memberships.filter(
            profile=profile,
        ).first()

        if membership is None:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method in ('PUT', 'PATCH'):
            return obj.author == profile

        if request.method == 'DELETE':
            return membership.role == Roles.admin or obj.task.team.owner == profile

        return False
