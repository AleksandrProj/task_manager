import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_user_list_contains_only_active_users_and_public_fields(
    jwt_client, user, django_user_model
):
    other = django_user_model.objects.create_user(
        username="other", email="other@example.com"
    )
    django_user_model.objects.create_user(username="inactive", is_active=False)

    response = jwt_client.get(reverse("user-list"))

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {"id": user.pk, "username": user.username},
        {"id": other.pk, "username": other.username},
    ]


def test_user_list_is_paginated(jwt_client, user, django_user_model):
    others = django_user_model.objects.bulk_create(
        [django_user_model(username=f"user_{index}") for index in range(20)]
    )

    first = jwt_client.get(reverse("user-list"))
    second = jwt_client.get(reverse("user-list"), {"page": 2})

    assert first.status_code == 200
    assert first.data["count"] == 21
    assert first.data["next"] is not None
    assert [item["id"] for item in first.data["results"]] == [
        user.pk,
        *(other.pk for other in others[:19]),
    ]
    assert second.status_code == 200
    assert second.data["results"] == [
        {"id": others[-1].pk, "username": others[-1].username}
    ]
    assert second.data["next"] is None


def test_me_returns_authenticated_users_profile(jwt_client, user, django_user_model):
    other = django_user_model.objects.create_user(username="other")

    response = jwt_client.get(reverse("user-me"), {"id": other.pk})

    assert response.status_code == 200
    assert response.data == {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@pytest.mark.parametrize("route", ["user-list", "user-me"])
def test_users_require_authentication(route):
    response = APIClient().get(reverse(route))

    assert response.status_code == 401
    assert response["WWW-Authenticate"].startswith("Bearer")


@pytest.mark.parametrize("route", ["user-list", "user-me"])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_user_api_is_read_only(jwt_client, user, route, method, django_user_model):
    response = getattr(jwt_client, method)(
        reverse(route), {"username": "changed", "is_staff": True}, format="json"
    )

    assert response.status_code == 405
    user.refresh_from_db()
    assert user.username == "alex"
    assert user.is_staff is False
    assert django_user_model.objects.count() == 1


def test_session_login_still_works(user):
    client = APIClient()
    client.force_login(user)

    response = client.get(reverse("user-me"))

    assert response.status_code == 200
    assert response.data["id"] == user.pk
