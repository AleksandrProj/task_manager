import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from tasks.models import CommentModel, TaskModel

pytestmark = pytest.mark.django_db


def test_create_comment_assigns_current_user(api_client, task, creator):
    response = api_client.post(
        reverse("comment-list"),
        {"task": task.pk, "text": "New comment"},
        format="json",
    )

    assert response.status_code == 201
    comment = CommentModel.objects.get(pk=response.data["id"])
    assert comment.author == creator
    assert comment.task == task
    assert comment.text == "New comment"
    assert response.data["author"] == creator.pk
    assert response.data["created_at"] is not None
    assert response.data["updated_at"] is not None


@pytest.mark.parametrize("method", ["post", "put"])
def test_comment_author_and_server_fields_cannot_be_spoofed(
    api_client, comment, creator, django_user_model, method
):
    other = django_user_model.objects.create_user(username="other")
    url = (
        reverse("comment-list")
        if method == "post"
        else reverse("comment-detail", args=[comment.pk])
    )
    response = getattr(api_client, method)(
        url,
        {
            "id": 999999,
            "task": comment.task_id,
            "text": "Updated",
            "author": other.pk,
            "created_at": "2000-01-01T00:00:00Z",
            "updated_at": "2000-01-01T00:00:00Z",
        },
        format="json",
    )

    assert response.status_code == (201 if method == "post" else 200)
    saved = CommentModel.objects.get(pk=response.data["id"])
    assert saved.author == creator
    assert saved.pk != 999999
    assert saved.created_at.year != 2000
    assert saved.updated_at.year != 2000
    if method == "put":
        assert saved.pk == comment.pk
        assert saved.created_at == comment.created_at


def test_empty_comment_list(api_client):
    response = api_client.get(reverse("comment-list"))

    assert response.status_code == 200
    assert response.data == {"count": 0, "next": None, "previous": None, "results": []}


def test_comment_list_is_paginated_and_ordered(api_client, task, creator):
    comments = CommentModel.objects.bulk_create(
        [CommentModel(task=task, author=creator, text=str(i)) for i in range(11)]
    )
    response = api_client.get(reverse("comment-list"))
    second_page = api_client.get(reverse("comment-list"), {"page": 2})

    assert response.status_code == 200
    assert response.data["count"] == 11
    assert response.data["next"] is not None
    assert [item["id"] for item in response.data["results"]] == [
        comment.pk for comment in comments[:10]
    ]
    assert second_page.status_code == 200
    assert [item["id"] for item in second_page.data["results"]] == [comments[10].pk]
    assert second_page.data["next"] is None


@pytest.mark.parametrize("method", ["post", "put"])
@pytest.mark.parametrize("text", ["", " \n\t ", None, "a" * 501])
def test_invalid_comment_text_is_rejected(api_client, comment, method, text):
    url = (
        reverse("comment-list")
        if method == "post"
        else reverse("comment-detail", args=[comment.pk])
    )
    response = getattr(api_client, method)(
        url, {"task": comment.task_id, "text": text}, format="json"
    )

    assert response.status_code == 400
    assert "text" in response.data
    assert CommentModel.objects.count() == 1
    comment.refresh_from_db()
    assert comment.text == "Comment"


@pytest.mark.parametrize("missing_field", ["task", "text"])
@pytest.mark.parametrize("method", ["post", "put"])
def test_required_comment_fields(api_client, comment, missing_field, method):
    payload = {"task": comment.task_id, "text": "Valid"}
    payload.pop(missing_field)
    url = (
        reverse("comment-list")
        if method == "post"
        else reverse("comment-detail", args=[comment.pk])
    )
    response = getattr(api_client, method)(url, payload, format="json")

    assert response.status_code == 400
    assert missing_field in response.data
    comment.refresh_from_db()
    assert comment.text == "Comment"
    assert CommentModel.objects.count() == 1


@pytest.mark.parametrize("task_id", [999999, None, "invalid"])
def test_invalid_comment_task_is_rejected(api_client, task_id):
    response = api_client.post(
        reverse("comment-list"),
        {"task": task_id, "text": "Comment"},
        format="json",
    )

    assert response.status_code == 400
    assert "task" in response.data
    assert not CommentModel.objects.exists()


def test_author_can_edit_comment(api_client, comment):
    response = api_client.put(
        reverse("comment-detail", args=[comment.pk]),
        {"task": comment.task_id, "text": "Edited"},
        format="json",
    )

    assert response.status_code == 200
    created_at = comment.created_at
    updated_at = comment.updated_at
    comment.refresh_from_db()
    assert comment.text == "Edited"
    assert comment.created_at == created_at
    assert comment.updated_at > updated_at


def test_author_can_delete_only_selected_comment(api_client, comment):
    other = CommentModel.objects.create(
        task=comment.task, author=comment.author, text="Other comment"
    )
    response = api_client.delete(reverse("comment-detail", args=[comment.pk]))

    assert response.status_code == 204
    assert list(CommentModel.objects.values_list("pk", flat=True)) == [other.pk]
    assert TaskModel.objects.filter(pk=comment.task_id).exists()


@pytest.mark.parametrize("method", ["put", "delete"])
@pytest.mark.parametrize("reader_kind", ["task_creator", "unrelated"])
def test_only_comment_author_can_change_it(
    api_client, task, django_user_model, method, reader_kind
):
    author = django_user_model.objects.create_user(username="commenter")
    comment = CommentModel.objects.create(task=task, author=author, text="Original")
    if reader_kind == "unrelated":
        api_client.force_authenticate(
            user=django_user_model.objects.create_user(username="unrelated")
        )
    response = getattr(api_client, method)(
        reverse("comment-detail", args=[comment.pk]),
        {"task": task.pk, "text": "Changed"},
        format="json",
    )

    assert response.status_code == 404
    comment.refresh_from_db()
    assert comment.text == "Original"
    assert comment.author == author


def test_comment_list_contains_only_current_users_comments(
    api_client, creator, django_user_model
):
    other = django_user_model.objects.create_user(username="other")
    task = TaskModel.objects.create(title="Other task", creator=other, assignee=creator)
    CommentModel.objects.create(task=task, author=other, text="Existing")

    listed = api_client.get(reverse("comment-list"))
    created = api_client.post(
        reverse("comment-list"), {"task": task.pk, "text": "Reply"}, format="json"
    )

    assert listed.status_code == 200
    assert listed.data["results"] == []
    assert created.status_code == 201
    assert created.data["author"] == creator.pk
    assert (
        api_client.get(reverse("comment-list")).data["results"][0]["id"]
        == (created.data["id"])
    )


@pytest.mark.parametrize(
    ("method", "detail"),
    [("get", False), ("post", False), ("put", True), ("delete", True)],
)
def test_anonymous_comment_requests_are_rejected(comment, method, detail):
    url = (
        reverse("comment-detail", args=[comment.pk])
        if detail
        else reverse("comment-list")
    )
    response = getattr(APIClient(), method)(
        url, {"task": comment.task_id, "text": "Changed"}, format="json"
    )

    assert response.status_code == 401
    comment.refresh_from_db()
    assert comment.text == "Comment"
    assert CommentModel.objects.count() == 1


@pytest.mark.parametrize("method", ["put", "delete"])
def test_missing_comment_returns_404(api_client, task, method):
    response = getattr(api_client, method)(
        reverse("comment-detail", args=[999999]),
        {"task": task.pk, "text": "Changed"},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.parametrize("method", ["get", "patch"])
def test_unsupported_comment_detail_methods_return_405(api_client, comment, method):
    response = getattr(api_client, method)(
        reverse("comment-detail", args=[comment.pk]),
        {"task": comment.task_id, "text": "Changed"},
        format="json",
    )

    assert response.status_code == 405
    comment.refresh_from_db()
    assert comment.text == "Comment"


def test_session_authentication_requires_csrf_for_comment_writes(creator, task):
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(creator)

    listed = client.get(reverse("comment-list"))
    created = client.post(
        reverse("comment-list"), {"task": task.pk, "text": "New"}, format="json"
    )

    assert listed.status_code == 200
    assert created.status_code == 403
    assert not CommentModel.objects.exists()
