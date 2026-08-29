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

from profiles.views import ProfileViewSet
from tasks.views import TaskViewSet
from teams.views import TeamViewSet, MembershipViewSet
from rest_framework_nested.routers import NestedSimpleRouter

router = routers.DefaultRouter()
router.register('teams', TeamViewSet, 'teams')
router.register('users', ProfileViewSet, 'users')

router.register('tasks', TaskViewSet, 'tasks')
teams_router = NestedSimpleRouter(router, r'teams', lookup='team')
teams_router.register(r'members', MembershipViewSet, basename='team-members')
teams_router.register(
    r'tasks',
    TaskViewSet,
    basename='team-tasks',
)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(teams_router.urls)),
    path("api/v1/auth/", include("rest_framework.urls"), name="api_v1"),

    # path('auth/login/', LoginView.as_view(
    #    template_name='registration/login.html'), name='login'),
    # path('auth/logout/', LogoutView.as_view(next_page='login'), name='logout'),
    # path('auth/password/', PasswordChangeView.as_view(
    #    template_name='registration/pwd_change.html', success_url='login'), name='password_change'),

    path('admin/', admin.site.urls),
]
