from django.db.models import Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import Task, TaskStatus, TaskComment, TaskRating
from tasks.permissions import TaskPermissions, TaskCommentPermissions, TaskRatingPermissions
# from tasks.permissions import CanEditTask
from tasks.serializers import TaskSerializer, TaskUpdateSerializer, TaskCreateSerializer, TaskShortSerializer
from tasks.serializers.TaskComment import TaskCommentSerializer, TaskCommentShortSerializer, TaskCommentCreateSerializer
from tasks.serializers.TaskRating import TaskRatingSerializer, TaskRatingShortSerializer, TaskRatingCreateSerializer
from teams.models import Team


# Create your views here.


class TaskViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Task.objects.all()

        team_id = self.kwargs.get('team_pk')
        if team_id is None:
            team_id = self.request.GET.get('team')
        queryset = queryset.filter(team__memberships__profile=self.request.user.profile)
        if team_id is not None:
            queryset = queryset.filter(team_id=team_id)
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
        if self.action in ('update', 'partial_update'):
            return TaskUpdateSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'retrieve':
            return TaskSerializer
        elif self.action == 'list':
            return TaskShortSerializer

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


class TaskRatingViewSet(viewsets.ModelViewSet):
    permission_classes = [TaskRatingPermissions]

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
        queryset = (
            TaskRating.objects
            .select_related('author', 'task', 'task__team', 'task__assignee')
        )

        task_id = self.kwargs.get('task_pk')
        if task_id is None:
            task_id = self.request.GET.get('task')
        if task_id is not None:
            queryset = queryset.filter(task_id=task_id)
        received = self.request.GET.get('received')
        created = self.request.GET.get('created')

        if received == 'me':
            queryset = queryset.filter(
                task__assignee=self.request.user.profile,
            )
        if created == 'me':
            queryset = queryset.filter(
                author=self.request.user.profile,
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TaskRatingCreateSerializer
        elif self.action == 'retrieve':
            return TaskRatingSerializer
        return TaskRatingShortSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user.profile,
            task=self.get_task(),
        )

    @action(detail=False, methods=['get'], url_path='avg')
    def avg_score(self, request, *args, **kwargs):
        avg_rating = (
            TaskRating.objects
            .filter(task=self.get_task())
            .aggregate(Avg("score", default=0))
        )
        return Response({
            'average_score': avg_rating['score__avg'],
        })
