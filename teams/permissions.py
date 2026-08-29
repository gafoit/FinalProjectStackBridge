from rest_framework.permissions import BasePermission

from teams.models import Membership, Roles, role_priority


class MembershipPerms(BasePermission):
    def has_permission(self, request, view):
        if view.action in ('list', 'retrieve'):
            team_id = view.kwargs.get('team_pk')
            if not team_id:
                return False
            return Membership.objects.filter(
                team_id=team_id,
                profile=request.user.profile
            ).exists()
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        current = Membership.objects.filter(
            team=obj.team,
            profile=request.user.profile,
        ).first()

        if current is None:
            return False

        # Можно работать со своей membership
        if obj.profile == request.user.profile:
            return True

        current_priority = role_priority[current.role]
        target_priority = role_priority[obj.role]

        if view.action in ('update', 'partial_update'):
            new_role = request.data.get('role')

            if new_role is None:
                return current_priority >= role_priority[Roles.admin]

            new_priority = role_priority.get(new_role)

            if new_priority is None:
                return False

            return (
                    current_priority >= target_priority
                    and new_priority <= current_priority
            )

        if view.action == 'destroy':
            return (
                    current_priority >= target_priority
                    and current.role != Roles.member
            )
        return True


class TeamPerms(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'retrieve':
            team_id = view.kwargs.get('pk')

            if not team_id:
                return False
            return Membership.objects.filter(
                team_id=team_id,
                profile=request.user.profile
            ).exists()

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        profile = request.user.profile

        try:
            current_membership = Membership.objects.get(team=obj, profile=profile)
        except Membership.DoesNotExist:
            return False

        if view.action in ('update', 'partial_update'):
            return current_membership.role in (Roles.admin, Roles.owner)
        if view.action == 'destroy':
            return current_membership.role == Roles.owner
        return True
