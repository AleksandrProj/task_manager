import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from tasks.models import CommentModel, TaskModel


@pytest.fixture
def task(creator):
    return TaskModel.objects.create(title="First task", creator=creator)


@pytest.fixture
def comment(task, creator):
    return CommentModel.objects.create(task=task, author=creator, text="Comment")


@pytest.fixture
def assignee(django_user_model):
    return django_user_model.objects.create_user(username="assignee")


@pytest.fixture
def assigned_task(task, assignee):
    task.assignee = assignee
    task.save()
    return task


@pytest.fixture
def assignee_client(assignee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(assignee)}")
    return client
