from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from tasks.models import Task, TaskStatus, TaskComment, TaskRating
from tasks.permissions import TaskPermissions
# from tasks.permissions import CanEditTask
from tasks.serializers import TaskSerializer, TaskUpdateSerializer, TaskCreateSerializer
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
