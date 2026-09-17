import pytest
from rest_framework.test import APIClient


@pytest.fixture
def creator(django_user_model):
    return django_user_model.objects.create_user(username="creator")


@pytest.fixture
def api_client(creator):
    client = APIClient()
    client.force_authenticate(user=creator)
    return client
