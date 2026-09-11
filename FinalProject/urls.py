"""
URL configuration for FinalProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from meetups.views import MeetupViewSet
from ya_calendar.views import CalendarView
from profiles.views import ProfileViewSet
from tasks.views import TaskViewSet, TaskCommentViewSet, TaskRatingViewSet
from teams.views import TeamViewSet, MembershipViewSet, TeamTaskCommentsRedirectView, TeamTaskRatingRedirectView
from rest_framework_nested.routers import NestedSimpleRouter

router = routers.DefaultRouter()
router.register('teams', TeamViewSet, 'teams')
router.register('users', ProfileViewSet, 'users')
router.register('tasks', TaskViewSet, 'tasks')

router.register('evaluations', TaskRatingViewSet, 'evaluations')

tasks_router = NestedSimpleRouter(router, r'tasks', lookup='task')
tasks_router.register(r'comments', TaskCommentViewSet, basename='task-comments')
tasks_router.register(r'evaluations', TaskRatingViewSet, basename='task-ratings')

# NestedRouters для красоты.
teams_router = NestedSimpleRouter(router, r'teams', lookup='team')
teams_router.register(
    r'members',
    MembershipViewSet,
    basename='team-members'
)
teams_router.register(
    r'tasks',
    TaskViewSet,
    basename='team-tasks',
)
teams_router.register(
    'meetups',
    MeetupViewSet,
    basename='team-meetups'
)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(teams_router.urls)),
    path('api/v1/', include(tasks_router.urls)),
    path("api/v1/calendar/", CalendarView.as_view(), name="calendar"),
    path('api/v1/teams/<int:team_id>/tasks/<int:task_id>/comments/',
         TeamTaskCommentsRedirectView.as_view(),
         name='redirect-team-task-comments'),
    path('api/v1/teams/<int:team_id>/tasks/<int:task_id>/evaluations/',
         TeamTaskRatingRedirectView.as_view(),
         name='redirect-team-task-evaluations'),
    path("api/v1/auth/", include("rest_framework.urls"), name="api_v1"),

    path('admin/', admin.site.urls),
]
