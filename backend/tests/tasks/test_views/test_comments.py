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

    assert response.status_code == (403 if reader_kind == "task_creator" else 404)
    comment.refresh_from_db()
    assert comment.text == "Original"
    assert comment.author == author


def test_assignee_can_read_other_authors_comments_and_reply(
    api_client, creator, django_user_model
):
    other = django_user_model.objects.create_user(username="other")
    task = TaskModel.objects.create(title="Other task", creator=other, assignee=creator)
    existing = CommentModel.objects.create(task=task, author=other, text="Existing")

    listed = api_client.get(reverse("comment-list"))
    created = api_client.post(
        reverse("comment-list"), {"task": task.pk, "text": "Reply"}, format="json"
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.data["results"]] == [existing.pk]
    assert created.status_code == 201
    assert created.data["author"] == creator.pk
    assert [
        item["id"] for item in api_client.get(reverse("comment-list")).data["results"]
    ] == [existing.pk, created.data["id"]]


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


def test_creator_reads_all_participants_comments_but_not_other_tasks(
    api_client, assigned_task, creator, assignee, django_user_model
):
    comments = CommentModel.objects.bulk_create(
        [
            CommentModel(task=assigned_task, author=creator, text="Question"),
            CommentModel(task=assigned_task, author=assignee, text="Reply"),
        ]
    )
    stranger = django_user_model.objects.create_user(username="stranger")
    hidden_task = TaskModel.objects.create(title="Private", creator=stranger)
    CommentModel.objects.create(task=hidden_task, author=stranger, text="Hidden")

    response = api_client.get(reverse("comment-list"))

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert [item["id"] for item in response.data["results"]] == [
        comment.pk for comment in comments
    ]


def test_task_filter_is_applied_before_pagination(api_client, task, creator):
    other_task = TaskModel.objects.create(title="Other", creator=creator)
    CommentModel.objects.bulk_create(
        [CommentModel(task=other_task, author=creator, text="Other") for _ in range(12)]
    )
    comments = CommentModel.objects.bulk_create(
        [CommentModel(task=task, author=creator, text=str(i)) for i in range(11)]
    )

    first = api_client.get(reverse("comment-list"), {"task": task.pk})
    second = api_client.get(first.data["next"])

    assert first.status_code == second.status_code == 200
    assert first.data["count"] == second.data["count"] == 11
    assert f"task={task.pk}" in first.data["next"]
    assert [item["id"] for item in first.data["results"]] == [
        comment.pk for comment in comments[:10]
    ]
    assert [item["id"] for item in second.data["results"]] == [comments[-1].pk]


@pytest.mark.parametrize("task_id", ["invalid", "", "0", "-1", "1.5"])
def test_invalid_task_filter_returns_400(api_client, task_id):
    response = api_client.get(reverse("comment-list"), {"task": task_id})

    assert response.status_code == 400
    assert "task" in response.data


def test_unrelated_user_cannot_read_or_create_comments(
    api_client, comment, django_user_model
):
    api_client.force_authenticate(
        django_user_model.objects.create_user(username="stranger")
    )
    for params in ({}, {"task": comment.task_id}, {"task": 999999}):
        response = api_client.get(reverse("comment-list"), params)
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    created = api_client.post(
        reverse("comment-list"),
        {"task": comment.task_id, "text": "Unauthorized"},
        format="json",
    )

    assert created.status_code == 400
    assert "task" in created.data
    assert CommentModel.objects.count() == 1


@pytest.mark.parametrize("method", ["put", "delete"])
def test_assignee_cannot_change_creators_comment(
    assignee_client, assigned_task, comment, method
):
    response = getattr(assignee_client, method)(
        reverse("comment-detail", args=[comment.pk]),
        {"task": assigned_task.pk, "text": "Changed"},
        format="json",
    )

    assert response.status_code == 403
    comment.refresh_from_db()
    assert comment.text == "Comment"


def test_assignee_can_edit_and_delete_own_comment(
    assignee_client, assigned_task, assignee
):
    comment = CommentModel.objects.create(
        task=assigned_task, author=assignee, text="Original"
    )
    url = reverse("comment-detail", args=[comment.pk])

    updated = assignee_client.put(
        url, {"task": assigned_task.pk, "text": "Updated"}, format="json"
    )
    assert updated.status_code == 200
    comment.refresh_from_db()
    assert comment.text == "Updated"

    assert assignee_client.delete(url).status_code == 204
    assert not CommentModel.objects.filter(pk=comment.pk).exists()


@pytest.mark.parametrize("reassign", [False, True])
def test_former_assignee_loses_access_to_own_comments(
    assignee_client, assigned_task, assignee, django_user_model, reassign
):
    comment = CommentModel.objects.create(
        task=assigned_task, author=assignee, text="Original"
    )
    new_assignee = django_user_model.objects.create_user(username="replacement")
    assigned_task.assignee = new_assignee if reassign else None
    assigned_task.save()

    listed = assignee_client.get(reverse("comment-list"), {"task": assigned_task.pk})
    created = assignee_client.post(
        reverse("comment-list"),
        {"task": assigned_task.pk, "text": "New"},
        format="json",
    )
    assert listed.status_code == 200
    assert listed.data["count"] == 0
    assert created.status_code == 400
    for method in ("put", "delete"):
        response = getattr(assignee_client, method)(
            reverse("comment-detail", args=[comment.pk]),
            {"task": assigned_task.pk, "text": "Changed"},
            format="json",
        )
        assert response.status_code == 404

    comment.refresh_from_db()
    assert comment.text == "Original"
    if reassign:
        assignee_client.force_authenticate(new_assignee)
        response = assignee_client.get(
            reverse("comment-list"), {"task": assigned_task.pk}
        )
        assert [item["id"] for item in response.data["results"]] == [comment.pk]


def test_comment_cannot_be_moved_to_inaccessible_task(
    api_client, comment, django_user_model
):
    stranger = django_user_model.objects.create_user(username="stranger")
    target = TaskModel.objects.create(title="Private", creator=stranger)
    original_task_id = comment.task_id

    response = api_client.put(
        reverse("comment-detail", args=[comment.pk]),
        {"task": target.pk, "text": "Changed"},
        format="json",
    )

    assert response.status_code == 400
    assert "task" in response.data
    comment.refresh_from_db()
    assert comment.task_id == original_task_id
    assert comment.text == "Comment"
