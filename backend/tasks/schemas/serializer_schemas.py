from drf_spectacular.utils import OpenApiExample, OpenApiResponse

from app.schemas import error_responses, example_response
from tasks.serializers import (
    CommentFilterSerializer,
    CommentSerializer,
    TasksSerializer,
    TaskStatusSerializer,
)

TASK = {
    "id": 1,
    "title": "Prepare API documentation",
    "description": "Add request examples and error responses to Swagger.",
    "status": "new",
    "priority": "medium",
    "creator": 1,
    "assignee": 2,
    "created_at": "2026-09-17T10:00:00Z",
    "updated_at": "2026-09-17T10:00:00Z",
}

COMMENT = {
    "id": 1,
    "text": "Started working on the documentation.",
    "task": 1,
    "author": 2,
    "created_at": "2026-09-17T10:05:00Z",
    "updated_at": "2026-09-17T10:05:00Z",
}

list_task = {
    "summary": "List my tasks",
    "description": "Tasks created by or assigned to the current user, newest first. "
    "20 tasks per page. Use the page query parameter or the next/previous links.",
    "responses": {
        200: example_response(TasksSerializer, TASK, "Paginated task list."),
        **error_responses(401, 404),
    },
}

create_task = {
    "summary": "Create a task",
    "description": "Only title is required. The server sets creator and timestamps. "
    "Assignee must be an active user other than the creator; null is allowed. "
    "Example IDs are illustrative: replace them with existing user IDs.",
    "examples": [
        OpenApiExample(
            "Minimal task", value={"title": "Prepare documentation"}, request_only=True
        ),
        OpenApiExample(
            "Task with assignee",
            value={
                "title": TASK["title"],
                "description": TASK["description"],
                "status": "new",
                "priority": "medium",
                "assignee": 2,
            },
            request_only=True,
        ),
        OpenApiExample(
            "Invalid assignment",
            value={"assignee": ["The task creator cannot be its assignee."]},
            response_only=True,
            status_codes=["400"],
        ),
    ],
    "responses": {
        201: example_response(TasksSerializer, TASK, "Task created."),
        **error_responses(400, 401, 403),
    },
}

detail_task = {
    "summary": "Get a task",
    "description": "Available to the creator and current assignee. "
    "Other users receive 404.",
    "responses": {
        200: example_response(TasksSerializer, TASK, "Task details."),
        **error_responses(401, 404),
    },
}

update_task = {
    "summary": "Edit a task",
    "description": "Creator only. PUT requires title; omitted optional fields retain "
    "their values. Send assignee: null to clear the assignment. Creator, ID and "
    "timestamps are read-only. Assignees must use the separate status endpoint.",
    "examples": [
        OpenApiExample(
            "Edit task",
            value={
                "title": TASK["title"],
                "description": "Update the Swagger examples.",
                "priority": "high",
                "status": "in_progress",
                "assignee": 2,
            },
            request_only=True,
        ),
        OpenApiExample(
            "Remove assignee",
            value={
                "title": TASK["title"],
                "assignee": None,
            },
            request_only=True,
        ),
    ],
    "responses": {
        200: example_response(
            TasksSerializer,
            {
                **TASK,
                "description": "Update the Swagger examples.",
                "priority": "high",
                "status": "in_progress",
                "updated_at": "2026-09-17T11:00:00Z",
            },
            "Updated task.",
        ),
        **error_responses(400, 401, 403, 404),
    },
}

delete_task = {
    "summary": "Delete a task",
    "description": "Creator only. Related comments are deleted as well. "
    "No request or response body is used.",
    "responses": {
        204: OpenApiResponse(
            description="Task and its comments deleted. No response body."
        ),
        **error_responses(401, 403, 404),
    },
}

set_task_status = {
    "summary": "Change task status",
    "description": "Creator or current assignee only. The status field is required; "
    "all additional fields are rejected. Allowed values: new, in_progress, done. "
    "Invalid requests do not change the task. A former assignee receives 404.",
    "examples": [
        OpenApiExample(
            "Start work", value={"status": "in_progress"}, request_only=True
        ),
        OpenApiExample("Complete task", value={"status": "done"}, request_only=True),
        OpenApiExample(
            "Additional fields rejected",
            value={"non_field_errors": ["Only the status field is allowed."]},
            response_only=True,
            status_codes=["400"],
        ),
    ],
    "responses": {
        200: example_response(
            TaskStatusSerializer, {"status": "done"}, "Updated status."
        ),
        **error_responses(400, 401, 403, 404),
    },
}

list_comment = {
    "summary": "List comments on accessible tasks",
    "description": "All comments on tasks created by or assigned to the current "
    "user, oldest first. Optionally filter by task ID with ?task=1. Hidden or "
    "missing tasks return an empty list. Invalid task IDs return 400. "
    "10 comments per page. Use the page query parameter or next/previous links.",
    "parameters": [CommentFilterSerializer],
    "responses": {
        200: example_response(CommentSerializer, COMMENT, "Paginated comment list."),
        **error_responses(400, 401, 404),
    },
}

create_comment = {
    "summary": "Create a comment",
    "description": "The task creator or current assignee can comment. Both text "
    "and an accessible task ID are required. Text must not be "
    "blank and may contain up to 500 characters. The server sets author and dates. "
    "Replace the example task ID with an existing task ID.",
    "examples": [
        OpenApiExample(
            "Add comment", value={"task": 1, "text": COMMENT["text"]}, request_only=True
        ),
        OpenApiExample(
            "Blank comment",
            value={"text": ["This field may not be blank."]},
            response_only=True,
            status_codes=["400"],
        ),
    ],
    "responses": {
        201: example_response(CommentSerializer, COMMENT, "Comment created."),
        **error_responses(400, 401, 403),
    },
}

update_comment = {
    "summary": "Edit a comment",
    "description": "Author only. PUT requires both text and task. The task reference "
    "can also be changed to another accessible task. Author, ID and timestamps "
    "are read-only. Editing another author's comment returns 403. Comments on "
    "inaccessible tasks return 404, even for their original author.",
    "examples": [
        OpenApiExample(
            "Edit comment",
            value={"task": 1, "text": "Request examples are ready for review."},
            request_only=True,
        )
    ],
    "responses": {
        200: example_response(
            CommentSerializer,
            {
                **COMMENT,
                "text": "Request examples are ready for review.",
                "updated_at": "2026-09-17T11:05:00Z",
            },
            "Updated comment.",
        ),
        **error_responses(400, 401, 403, 404),
    },
}

delete_comment = {
    "summary": "Delete a comment",
    "description": "Author only. The related task is preserved. No request or "
    "response body is used. Deleting another author's comment returns 403. "
    "Comments on inaccessible tasks return 404, even for their original author.",
    "responses": {
        204: OpenApiResponse(description="Comment deleted. No response body."),
        **error_responses(401, 403, 404),
    },
}
