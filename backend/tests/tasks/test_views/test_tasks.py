import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from tasks.models import CommentModel, TaskModel

pytestmark = pytest.mark.django_db


def test_empty_task_list(api_client):
    response = api_client.get(reverse("task-list"))

    assert response.status_code == 200
    assert response.data == {"count": 0, "next": None, "previous": None, "results": []}


def test_task_list_is_paginated_and_ordered(api_client, creator):
    tasks = TaskModel.objects.bulk_create(
        [TaskModel(title=f"Task {index}", creator=creator) for index in range(21)]
    )

    response = api_client.get(reverse("task-list"))
    second_page = api_client.get(reverse("task-list"), {"page": 2})

    assert response.status_code == 200
    assert response.data["count"] == 21
    assert response.data["next"] is not None
    assert [item["id"] for item in response.data["results"]] == [
        task.pk for task in reversed(tasks[1:])
    ]
    assert second_page.status_code == 200
    assert [item["id"] for item in second_page.data["results"]] == [tasks[0].pk]
    assert second_page.data["next"] is None


def test_create_task_assigns_author_and_defaults(api_client, creator):
    response = api_client.post(
        reverse("task-list"), {"title": "New task"}, format="json"
    )

    assert response.status_code == 201
    task = TaskModel.objects.get(pk=response.data["id"])
    assert task.title == "New task"
    assert task.creator == creator
    assert response.data["creator"] == creator.pk
    assert response.data["description"] == ""
    assert response.data["status"] == "new"
    assert response.data["priority"] == "low"
    assert response.data["assignee"] is None
    assert response.data["created_at"] is not None
    assert response.data["updated_at"] is not None


def test_create_task_with_all_editable_fields(api_client, django_user_model):
    assignee = django_user_model.objects.create_user(username="assignee")
    payload = {
        "title": "New task",
        "description": "Description",
        "status": "in_progress",
        "priority": "high",
        "assignee": assignee.pk,
    }

    response = api_client.post(reverse("task-list"), payload, format="json")

    assert response.status_code == 201
    assert {key: response.data[key] for key in payload} == payload


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({}, "title"),
        ({"title": ""}, "title"),
        ({"title": "   "}, "title"),
        ({"title": None}, "title"),
        ({"title": "a" * 151}, "title"),
        ({"title": "Valid", "description": "a" * 501}, "description"),
        ({"title": "Valid", "status": "invalid"}, "status"),
        ({"title": "Valid", "priority": "invalid"}, "priority"),
    ],
)
def test_create_task_rejects_invalid_data(api_client, payload, field):
    response = api_client.post(reverse("task-list"), payload, format="json")

    assert response.status_code == 400
    assert field in response.data
    assert not TaskModel.objects.exists()


@pytest.mark.parametrize("method", ["post", "put"])
@pytest.mark.parametrize("assignee_kind", ["creator", "inactive", "missing"])
def test_api_rejects_invalid_assignee(
    api_client, task, creator, django_user_model, method, assignee_kind
):
    assignee_ids = {
        "creator": creator.pk,
        "inactive": django_user_model.objects.create_user(
            username="inactive", is_active=False
        ).pk,
        "missing": 999999,
    }
    url = (
        reverse("task-list")
        if method == "post"
        else reverse("task-detail", args=[task.pk])
    )
    response = getattr(api_client, method)(
        url,
        {"title": "Changed", "assignee": assignee_ids[assignee_kind]},
        format="json",
    )

    assert response.status_code == 400
    assert "assignee" in response.data
    assert TaskModel.objects.count() == 1
    task.refresh_from_db()
    assert task.title == "First task"
    assert task.assignee is None


def test_retrieve_task(api_client, task):
    response = api_client.get(reverse("task-detail", args=[task.pk]))

    assert response.status_code == 200
    assert response.data["id"] == task.pk
    assert response.data["title"] == task.title


def test_replace_task(api_client, task, django_user_model):
    assignee = django_user_model.objects.create_user(username="assignee")
    payload = {
        "title": "Replaced",
        "description": "New description",
        "status": "in_progress",
        "priority": "high",
        "assignee": assignee.pk,
    }

    response = api_client.put(
        reverse("task-detail", args=[task.pk]), payload, format="json"
    )

    assert response.status_code == 200
    task.refresh_from_db()
    assert task.title == "Replaced"
    assert task.assignee == assignee
    assert {key: response.data[key] for key in payload} == payload


def test_put_requires_title(api_client, task):
    response = api_client.put(
        reverse("task-detail", args=[task.pk]), {"status": "done"}, format="json"
    )

    assert response.status_code == 400
    assert "title" in response.data
    task.refresh_from_db()
    assert task.status == "new"


def test_task_patch_is_not_supported(api_client, task):
    response = api_client.patch(
        reverse("task-detail", args=[task.pk]), {"status": "done"}, format="json"
    )

    assert response.status_code == 405
    task.refresh_from_db()
    assert task.status == "new"


def test_put_can_update_status(api_client, task):
    response = api_client.put(
        reverse("task-detail", args=[task.pk]),
        {"title": task.title, "status": "done"},
        format="json",
    )

    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == "done"
    assert task.title == "First task"
    assert task.priority == "low"


def test_put_can_clear_assignee(api_client, task, django_user_model):
    task.assignee = django_user_model.objects.create_user(username="assignee")
    task.save()

    response = api_client.put(
        reverse("task-detail", args=[task.pk]),
        {"title": task.title, "assignee": None},
        format="json",
    )

    assert response.status_code == 200
    task.refresh_from_db()
    assert task.assignee is None


@pytest.mark.parametrize("method", ["post", "put"])
def test_client_cannot_set_author_id_or_timestamps(
    api_client, task, creator, django_user_model, method
):
    other_user = django_user_model.objects.create_user(username="other")
    url = (
        reverse("task-list")
        if method == "post"
        else reverse("task-detail", args=[task.pk])
    )
    response = getattr(api_client, method)(
        url,
        {
            "id": 999999,
            "title": "Updated task",
            "creator": other_user.pk,
            "created_at": "2000-01-01T00:00:00Z",
            "updated_at": "2000-01-01T00:00:00Z",
        },
        format="json",
    )

    assert response.status_code == (201 if method == "post" else 200)
    saved_task = TaskModel.objects.get(pk=response.data["id"])
    assert saved_task.creator == creator
    assert saved_task.pk != 999999
    assert saved_task.created_at.year != 2000
    assert saved_task.updated_at.year != 2000
    if method == "put":
        assert saved_task.pk == task.pk
        assert saved_task.created_at == task.created_at


def test_delete_task_removes_comments(api_client, task, creator):
    CommentModel.objects.create(task=task, author=creator, text="Comment")

    response = api_client.delete(reverse("task-detail", args=[task.pk]))

    assert response.status_code == 204
    assert not TaskModel.objects.filter(pk=task.pk).exists()
    assert not CommentModel.objects.exists()


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_task_returns_404(api_client, method):
    response = getattr(api_client, method)(
        reverse("task-detail", args=[999999]),
        {"title": "Missing task"},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("method", "detail"),
    [
        ("get", False),
        ("post", False),
        ("get", True),
        ("put", True),
        ("delete", True),
    ],
)
def test_anonymous_requests_are_rejected(task, method, detail):
    url = reverse("task-detail", args=[task.pk]) if detail else reverse("task-list")
    response = getattr(APIClient(), method)(url, {"title": "Changed"}, format="json")

    assert response.status_code == 403
    task.refresh_from_db()
    assert task.title == "First task"
    assert TaskModel.objects.count() == 1


def test_other_user_can_read_tasks(task, django_user_model):
    client = APIClient()
    client.force_authenticate(
        user=django_user_model.objects.create_user(username="reader")
    )

    task_list = client.get(reverse("task-list"))
    detail = client.get(reverse("task-detail", args=[task.pk]))

    assert task_list.status_code == 200
    assert task_list.data["results"][0]["id"] == task.pk
    assert detail.status_code == 200


@pytest.mark.parametrize("method", ["put", "delete"])
def test_other_user_cannot_change_or_delete_task(task, django_user_model, method):
    client = APIClient()
    client.force_authenticate(
        user=django_user_model.objects.create_user(username="other")
    )

    response = getattr(client, method)(
        reverse("task-detail", args=[task.pk]), {"title": "Changed"}, format="json"
    )

    assert response.status_code == 403
    task.refresh_from_db()
    assert task.title == "First task"


def test_session_authentication_works_and_requires_csrf_for_writes(creator, task):
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(creator)

    response = client.get(reverse("task-list"))
    write = client.put(
        reverse("task-detail", args=[task.pk]), {"title": "Changed"}, format="json"
    )

    assert response.status_code == 200
    assert write.status_code == 403
    task.refresh_from_db()
    assert task.title == "First task"
