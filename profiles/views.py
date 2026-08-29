from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from profiles.models import Profile
from profiles.serializers.Profile import ProfileSerializer, ProfileCreateSerializer, ProfileDetailSerializer


# Create your views here.


class ProfileViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if self.action == 'list':
            return Profile.objects.all()
        elif self.action == 'me':
            return Profile.objects.get(user=self.request.user)
        else:
            return Profile.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ProfileCreateSerializer
        elif self.action in ['me', 'retrieve']:
            return ProfileDetailSerializer
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
        profile = self.get_queryset()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
