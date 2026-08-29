from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from tasks.models import Task, TaskStatus, TaskComment, TaskRating
from serializers import TaskSerializer


# Create your views here.


class TasksViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # А это созданных
        if self.action == 'created':
            return Task.objects.filter(created_by=self.request.user.profile)
        # список - тех задач которые назначены тебе
        if self.action == 'list':
            return Task.objects.filter(assignee=self.request.user.profile)

    def get_serializer_class(self):
        if action in ['created', 'list']:
            return TaskSerializer

    @action(detail=False, methods=['get'])
    def created(self):
        return Response(self.get_queryset(), status=status.HTTP_200_OK)
