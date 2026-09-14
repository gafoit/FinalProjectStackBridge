import pytest
from django.contrib.auth.models import User

from profiles.models import Profile


@pytest.mark.django_db
def test_profile_created_with_user():
    user = User.objects.create_user(
        username="test",
        password="password123",
    )

    assert Profile.objects.filter(user=user).exists()
