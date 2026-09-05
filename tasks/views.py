from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from tasks.models import Task, TaskStatus, TaskComment, TaskRating
from tasks.permissions import TaskPermissions, TaskCommentPermissions
# from tasks.permissions import CanEditTask
from tasks.serializers import TaskSerializer, TaskUpdateSerializer, TaskCreateSerializer
from tasks.serializers.TaskComment import TaskCommentSerializer, TaskCommentShortSerializer, TaskCommentCreateSerializer
from teams.models import Team


# Create your views here.


class TaskViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Task.objects.all()

        team_id = self.kwargs.get('team_pk')
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        else:

            queryset = queryset.filter(team__memberships__profile=self.request.user.profile)

            filter_team_id = self.request.query_params.get('team')

            if filter_team_id:
                queryset = queryset.filter(team_id=filter_team_id)
        # Чтобы можно было отделить таски которые мне нужно выполнить и которые я сделал для других
        assigned = self.request.GET.get('assigned')
        created = self.request.GET.get('created')

        if assigned == 'me':
            queryset = queryset.filter(
                assignee=self.request.user.profile
            )

        if created == 'me':
            queryset = queryset.filter(
                created_by=self.request.user.profile
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'update':
            return TaskUpdateSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        else:
            return TaskSerializer

    def get_permissions(self):
        return [TaskPermissions()]

    def perform_create(self, serializer):
        team_id = self.kwargs.get('team_pk')
        serializer.save(
            team_id=team_id,
            created_by=self.request.user.profile,
        )


class TaskCommentViewSet(viewsets.ModelViewSet):
    permission_classes = [TaskCommentPermissions]

    def get_task(self):
        task = get_object_or_404(
            Task.objects.select_related('team'),
            pk=self.kwargs['task_pk'],
        )

        if not task.team.memberships.filter(
                profile=self.request.user.profile,
        ).exists():
            raise PermissionDenied(
                'You are not a member of this team.'
            )

        return task

    def get_queryset(self):
        task = self.get_task()

        return (
            TaskComment.objects
            .filter(task=task)
            .select_related('author')
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TaskCommentCreateSerializer

        if self.action == 'retrieve':
            return TaskCommentSerializer

        return TaskCommentShortSerializer

    def perform_create(self, serializer):
        task = self.get_task()

        serializer.save(
            author=self.request.user.profile,
            task=task,
        )
