from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'username')


class ProfileDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ('username','email')


class UserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(allow_null=True,allow_blank=True)
    password1 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProfileCreateSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()

    class Meta:
        model = Profile
        fields = ('user',)

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password1 = user_data.pop('password1')
        password2 = user_data.pop('password2')
        if password1 != password2:
            raise serializers.ValidationError({'password': 'Пароли не совпадают'})
        user_data['password'] = password1
        new_user = User.objects.create_user(**user_data)
        new_profile = Profile.objects.create(user=new_user)
        return new_profile

