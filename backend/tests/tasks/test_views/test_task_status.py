import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from tasks.models import TaskModel

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ["creator", "assignee"])
@pytest.mark.parametrize("status", ["new", "in_progress", "done"])
def test_creator_and_assignee_can_change_only_status(
    api_client, assignee_client, assigned_task, role, status
):
    client = api_client if role == "creator" else assignee_client
    before = TaskModel.objects.values().get(pk=assigned_task.pk)

    response = client.put(
        reverse("task-status", args=[assigned_task.pk]),
        {"status": status},
        format="json",
    )

    assert response.status_code == 200
    assert response.data == {"status": status}
    after = TaskModel.objects.values().get(pk=assigned_task.pk)
    assert after.pop("status") == status
    assert after.pop("updated_at") > before.pop("updated_at")
    before.pop("status")
    assert after == before


@pytest.mark.parametrize(
    "payload", [{}, {"status": None}, {"status": ""}, {"status": "invalid"}, []]
)
def test_status_requires_valid_value(assignee_client, assigned_task, payload):
    before = TaskModel.objects.values().get(pk=assigned_task.pk)

    response = assignee_client.put(
        reverse("task-status", args=[assigned_task.pk]), payload, format="json"
    )

    assert response.status_code == 400
    assert TaskModel.objects.values().get(pk=assigned_task.pk) == before


@pytest.mark.parametrize(
    "extra",
    [
        {"title": "First task"},
        {"description": "Changed"},
        {"priority": "high"},
        {"creator": 999999},
        {"assignee": None},
        {"id": 999999},
        {"created_at": "2000-01-01T00:00:00Z"},
        {"updated_at": "2000-01-01T00:00:00Z"},
        {"unknown": "value"},
    ],
)
def test_status_rejects_extra_fields_without_partial_update(
    assignee_client, assigned_task, extra
):
    before = TaskModel.objects.values().get(pk=assigned_task.pk)

    response = assignee_client.put(
        reverse("task-status", args=[assigned_task.pk]),
        {"status": "done", **extra},
        format="json",
    )

    assert response.status_code == 400
    assert TaskModel.objects.values().get(pk=assigned_task.pk) == before


@pytest.mark.parametrize("method", ["put", "delete"])
def test_assignee_cannot_edit_or_delete_task(assignee_client, assigned_task, method):
    before = TaskModel.objects.values().get(pk=assigned_task.pk)

    response = getattr(assignee_client, method)(
        reverse("task-detail", args=[assigned_task.pk]),
        {"title": "Changed", "status": "done"},
        format="json",
    )

    assert response.status_code == 403
    assert TaskModel.objects.values().get(pk=assigned_task.pk) == before


def test_assignee_can_see_assigned_task(assignee_client, assigned_task, creator):
    TaskModel.objects.create(title="Unassigned", creator=creator)

    listed = assignee_client.get(reverse("task-list"))
    detail = assignee_client.get(reverse("task-detail", args=[assigned_task.pk]))

    assert listed.status_code == 200
    assert [item["id"] for item in listed.data["results"]] == [assigned_task.pk]
    assert detail.status_code == 200


def test_unrelated_user_cannot_change_status(assignee_client, task):
    response = assignee_client.put(
        reverse("task-status", args=[task.pk]), {"status": "done"}, format="json"
    )

    assert response.status_code == 404
    task.refresh_from_db()
    assert task.status == "new"


def test_missing_task_status_returns_404(assignee_client):
    response = assignee_client.put(
        reverse("task-status", args=[999999]), {"status": "done"}, format="json"
    )

    assert response.status_code == 404


def test_anonymous_user_cannot_change_status(assigned_task):
    response = APIClient().put(
        reverse("task-status", args=[assigned_task.pk]),
        {"status": "done"},
        format="json",
    )

    assert response.status_code == 401
    assigned_task.refresh_from_db()
    assert assigned_task.status == "new"


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_status_action_accepts_only_put(assignee_client, assigned_task, method):
    response = getattr(assignee_client, method)(
        reverse("task-status", args=[assigned_task.pk]),
        {"status": "done"},
        format="json",
    )

    assert response.status_code == 405
    assigned_task.refresh_from_db()
    assert assigned_task.status == "new"


@pytest.mark.parametrize("remove_assignment", [False, True])
def test_former_assignee_loses_access_after_reassignment(
    api_client, assignee_client, assigned_task, django_user_model, remove_assignment
):
    next_assignee = django_user_model.objects.create_user(username="next_assignee")
    changed = api_client.put(
        reverse("task-detail", args=[assigned_task.pk]),
        {
            "title": assigned_task.title,
            "assignee": None if remove_assignment else next_assignee.pk,
        },
        format="json",
    )
    assert changed.status_code == 200

    response = assignee_client.put(
        reverse("task-status", args=[assigned_task.pk]),
        {"status": "done"},
        format="json",
    )

    assert response.status_code == 404
    assigned_task.refresh_from_db()
    assert assigned_task.status == "new"
    if not remove_assignment:
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(next_assignee)}"
        )
        assert (
            client.put(
                reverse("task-status", args=[assigned_task.pk]),
                {"status": "done"},
                format="json",
            ).status_code
            == 200
        )
