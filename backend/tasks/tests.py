from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from tasks.models import CommentModel, TasksModel

pytestmark = pytest.mark.django_db


def test_task_can_be_created_without_assignee_or_description(creator):
    task = TasksModel(title="First task", creator=creator)
    task.full_clean()
    task.save()
    task.refresh_from_db()

    assert task.assignee is None
    assert task.description == ""
    assert task.status == TasksModel.Status.NEW
    assert task.priority == TasksModel.Priority.LOW
    assert task.created_at is not None
    assert task.updated_at is not None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", ""),
        ("title", None),
        ("title", "a" * 151),
        ("status", "invalid"),
        ("priority", "invalid"),
    ],
)
def test_task_rejects_invalid_fields(task, field, value):
    setattr(task, field, value)

    with pytest.raises(ValidationError, match=field):
        task.full_clean()


def test_deleting_assignee_keeps_task(task, django_user_model):
    assignee = django_user_model.objects.create_user(username="assignee")
    task.assignee = assignee
    task.save()

    assignee.delete()
    task.refresh_from_db()

    assert task.assignee is None


@pytest.mark.parametrize("existing", [False, True])
def test_task_rejects_creator_as_assignee(creator, existing):
    task = TasksModel(title="First task", creator=creator)
    if existing:
        task.save()
    task.assignee = creator

    with pytest.raises(ValidationError) as exc_info:
        task.full_clean()

    assert exc_info.value.message_dict["assignee"] == [
        "The task creator cannot be its assignee."
    ]


def test_task_can_be_assigned_to_another_user(task, django_user_model):
    assignee = django_user_model.objects.create_user(username="assignee")
    task.assignee = assignee
    task.full_clean()
    task.save()
    task.refresh_from_db()

    assert task.assignee == assignee


def test_database_rejects_creation_with_creator_as_assignee(creator):
    with pytest.raises(IntegrityError, match="task_assignee_not_creator"):
        with transaction.atomic():
            TasksModel.objects.create(
                title="Invalid task", creator=creator, assignee=creator
            )


def test_database_rejects_saving_creator_as_assignee(task, creator):
    task.assignee = creator
    with pytest.raises(IntegrityError, match="task_assignee_not_creator"):
        with transaction.atomic():
            task.save()

    task.refresh_from_db()
    assert task.assignee is None


def test_database_rejects_updating_assignee_to_creator(task, creator):
    with pytest.raises(IntegrityError, match="task_assignee_not_creator"):
        with transaction.atomic():
            TasksModel.objects.filter(pk=task.pk).update(assignee=creator)

    task.refresh_from_db()
    assert task.assignee is None


def test_task_creator_cannot_be_deleted(task, creator):
    with pytest.raises(ProtectedError):
        creator.delete()

    assert TasksModel.objects.filter(pk=task.pk).exists()


def test_deleting_task_removes_only_its_comments(task, creator):
    CommentModel.objects.create(task=task, author=creator, text="First comment")
    other_task = TasksModel.objects.create(title="Other task", creator=creator)
    other_comment = CommentModel.objects.create(
        task=other_task, author=creator, text="Other comment"
    )

    task.delete()

    assert list(CommentModel.objects.values_list("pk", flat=True)) == [other_comment.pk]


def test_comment_author_cannot_be_deleted(task, django_user_model):
    author = django_user_model.objects.create_user(username="commenter")
    comment = CommentModel.objects.create(task=task, author=author, text="Comment")

    with pytest.raises(ProtectedError):
        author.delete()

    assert CommentModel.objects.filter(pk=comment.pk).exists()


@pytest.mark.parametrize("text", ["", "a" * 501])
def test_comment_rejects_invalid_text(task, creator, text):
    comment = CommentModel(task=task, author=creator, text=text)

    with pytest.raises(ValidationError, match="text"):
        comment.full_clean()


def test_task_can_be_completed_without_changing_creation_date(task, monkeypatch):
    created_at = task.created_at
    updated_at = created_at + timedelta(seconds=1)
    monkeypatch.setattr("django.utils.timezone.now", lambda: updated_at)

    task.status = TasksModel.Status.DONE
    task.full_clean()
    task.save()
    task.refresh_from_db()

    assert task.status == TasksModel.Status.DONE
    assert task.created_at == created_at
    assert task.updated_at == updated_at


def test_comment_can_be_edited_without_changing_creation_date(
    task, creator, monkeypatch
):
    comment = CommentModel.objects.create(task=task, author=creator, text="Before")
    created_at = comment.created_at
    updated_at = created_at + timedelta(seconds=1)
    monkeypatch.setattr("django.utils.timezone.now", lambda: updated_at)

    comment.text = "After"
    comment.full_clean()
    comment.save()
    comment.refresh_from_db()

    assert comment.text == "After"
    assert comment.created_at == created_at
    assert comment.updated_at == updated_at
