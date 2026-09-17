from datetime import timedelta
from secrets import token_urlsafe

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from tasks.models import CommentModel, TaskModel

pytestmark = pytest.mark.django_db


def test_login_returns_usable_tokens(user, credentials):
    client = APIClient()
    response = client.post(reverse("token_obtain_pair"), credentials, format="json")

    assert response.status_code == 200
    assert set(response.data) == {"access", "refresh"}
    access = AccessToken(response.data["access"])
    refresh = RefreshToken(response.data["refresh"])
    assert str(access["user_id"]) == str(user.pk)
    assert str(refresh["user_id"]) == str(user.pk)
    assert access["exp"] - access["iat"] == 15 * 60
    assert refresh["exp"] - refresh["iat"] == 24 * 60 * 60
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert client.get(reverse("user-me")).status_code == 200


@pytest.mark.parametrize("problem", ["password", "unknown_user", "inactive_user"])
def test_invalid_login_is_rejected(user, credentials, problem):
    if problem == "password":
        credentials["password"] = token_urlsafe(24)
    elif problem == "unknown_user":
        credentials["username"] = "unknown"
    else:
        user.is_active = False
        user.save()

    response = APIClient().post(
        reverse("token_obtain_pair"), credentials, format="json"
    )

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.parametrize("field", ["username", "password"])
def test_login_requires_credentials(credentials, field):
    credentials.pop(field)

    response = APIClient().post(
        reverse("token_obtain_pair"), credentials, format="json"
    )

    assert response.status_code == 400
    assert field in response.data


def test_refresh_returns_usable_access_token(user):
    refresh = RefreshToken.for_user(user)
    response = APIClient().post(
        reverse("token_refresh"), {"refresh": str(refresh)}, format="json"
    )

    assert response.status_code == 200
    assert set(response.data) == {"access"}
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    profile = client.get(reverse("user-me"))
    assert profile.status_code == 200
    assert profile.data["id"] == user.pk


@pytest.mark.parametrize("problem", ["expired", "malformed", "access", "tampered"])
def test_invalid_refresh_token_is_rejected(user, problem):
    refresh = RefreshToken.for_user(user)
    if problem == "expired":
        refresh.set_exp(lifetime=timedelta(seconds=-1))
        token = str(refresh)
    elif problem == "malformed":
        token = token_urlsafe(32)
    elif problem == "access":
        token = str(refresh.access_token)
    else:
        token = f"{refresh}tampered"

    response = APIClient().post(
        reverse("token_refresh"), {"refresh": token}, format="json"
    )

    assert response.status_code == 401
    assert "access" not in response.data


def test_refresh_requires_token():
    response = APIClient().post(reverse("token_refresh"), {}, format="json")

    assert response.status_code == 400
    assert "refresh" in response.data


@pytest.mark.parametrize("change", ["deactivate", "delete"])
def test_refresh_rejects_unavailable_user(user, change):
    refresh = str(RefreshToken.for_user(user))
    if change == "delete":
        user.delete()
    else:
        user.is_active = False
        user.save()

    response = APIClient().post(
        reverse("token_refresh"), {"refresh": refresh}, format="json"
    )

    assert response.status_code == 401


@pytest.mark.parametrize("route", ["user-me", "task-list", "comment-list"])
@pytest.mark.parametrize("problem", ["expired", "malformed", "refresh", "tampered"])
def test_invalid_bearer_token_cannot_access_api(user, route, problem):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    if problem == "expired":
        access.set_exp(lifetime=timedelta(seconds=-1))
        token = str(access)
    elif problem == "malformed":
        token = token_urlsafe(32)
    elif problem == "refresh":
        token = str(refresh)
    else:
        token = f"{access}tampered"
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = client.get(reverse(route))

    assert response.status_code == 401


@pytest.mark.parametrize("change", ["deactivate", "delete"])
def test_access_token_rejects_unavailable_user(jwt_client, user, change):
    if change == "delete":
        user.delete()
    else:
        user.is_active = False
        user.save()

    response = jwt_client.get(reverse("user-me"))

    assert response.status_code == 401


def test_jwt_supports_task_and_comment_lifecycle_without_csrf(user, credentials):
    client = APIClient(enforce_csrf_checks=True)
    login = client.post(reverse("token_obtain_pair"), credentials, format="json")
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    created = client.post(reverse("task-list"), {"title": "JWT task"}, format="json")
    assert created.status_code == 201
    task_id = created.data["id"]
    assert created.data["creator"] == user.pk
    comment = client.post(
        reverse("comment-list"), {"task": task_id, "text": "JWT comment"}, format="json"
    )
    assert comment.status_code == 201
    assert comment.data["author"] == user.pk
    changed = client.put(
        reverse("task-detail", args=[task_id]),
        {"title": "JWT task", "status": "done"},
        format="json",
    )
    assert changed.status_code == 200
    assert changed.data["status"] == "done"
    deleted = client.delete(reverse("task-detail", args=[task_id]))
    assert deleted.status_code == 204
    assert not TaskModel.objects.filter(pk=task_id).exists()
    assert not CommentModel.objects.filter(pk=comment.data["id"]).exists()


@pytest.mark.parametrize("resource", ["task", "comment"])
@pytest.mark.parametrize("method", ["put", "delete"])
def test_jwt_does_not_bypass_ownership(jwt_client, creator, resource, method):
    task = TaskModel.objects.create(title="Other task", creator=creator)
    comment = CommentModel.objects.create(task=task, author=creator, text="Original")
    obj = task if resource == "task" else comment
    response = getattr(jwt_client, method)(
        reverse(f"{resource}-detail", args=[obj.pk]),
        {"title": "Changed", "task": task.pk, "text": "Changed"},
        format="json",
    )

    assert response.status_code == 404
    task.refresh_from_db()
    comment.refresh_from_db()
    assert task.title == "Other task"
    assert comment.text == "Original"
