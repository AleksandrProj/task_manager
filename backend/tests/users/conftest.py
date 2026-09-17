from secrets import token_urlsafe

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def credentials():
    return {"username": "alex", "password": token_urlsafe(24)}


@pytest.fixture
def user(django_user_model, credentials):
    return django_user_model.objects.create_user(
        **credentials,
        email="alex@example.com",
        first_name="Alex",
        last_name="Tester",
    )


@pytest.fixture
def jwt_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
