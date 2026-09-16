import pytest

from tasks.models import TasksModel


@pytest.fixture
def creator(django_user_model):
    return django_user_model.objects.create_user(username="creator")


@pytest.fixture
def task(creator):
    return TasksModel.objects.create(title="First task", creator=creator)
