import pytest

from tasks.models import CommentModel, TaskModel


@pytest.fixture
def task(creator):
    return TaskModel.objects.create(title="First task", creator=creator)


@pytest.fixture
def comment(task, creator):
    return CommentModel.objects.create(task=task, author=creator, text="Comment")
