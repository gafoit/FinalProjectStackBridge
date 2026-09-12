from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer, ProfileCreateSerializer, ProfileDetailSerializer, \
    ProfilePasswordChangeSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Profile.objects.all()
        return Profile.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ProfileCreateSerializer
        elif self.action in ['me', 'retrieve']:
            return ProfileDetailSerializer
        elif self.action == 'change_password':
            return ProfilePasswordChangeSerializer
        else:
            return ProfileSerializer

    def get_permissions(self):
        if self.action == 'create':
            return []
        elif self.action in ['retrieve', 'list']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(self.request.user.profile)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='me/change_password')
    def change_password(self, request):
        serializer = self.get_serializer(
            data=request.data,
            instance=request.user.profile
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(HTTP_204_NO_CONTENT)
