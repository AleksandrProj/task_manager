from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

from tasks.models import CommentModel, TaskModel
from tasks.permissions import IsCommentAuthorOrReadOnly, IsTaskCreatorOrAssignee
from tasks.schemas import serializer_schemas
from tasks.serializers import (
    CommentFilterSerializer,
    CommentSerializer,
    TasksSerializer,
    TaskStatusSerializer,
)


class LinkPagination(PageNumberPagination):
    """
    Return the page links that the client can render without calculations.
    """

    def get_paginated_response_schema(self, schema):
        response_schema = super().get_paginated_response_schema(schema)
        response_schema["properties"]["pages"] = serializer_schemas.pagination
        response_schema["required"].append("pages")
        return response_schema

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "pages": self.get_page_links(),
                "results": data,
            }
        )

    def get_page_links(self):
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages
        visible_pages = {
            1,
            total_pages,
            *range(max(1, current_page - 2), min(total_pages, current_page + 2) + 1),
        }
        base_url = self.request.build_absolute_uri()
        return [
            {
                "number": number,
                "url": replace_query_param(base_url, self.page_query_param, number),
                "current": number == current_page,
            }
            for number in sorted(visible_pages)
        ]


class TaskPagination(LinkPagination):
    """
    Pagination for tasks.
    """

    page_size = 10


class CommentPagination(LinkPagination):
    """
    Pagination for comments.
    """

    page_size = 10


@extend_schema(tags=["Tasks"])
@extend_schema_view(
    list=extend_schema(**serializer_schemas.list_task),
    create=extend_schema(**serializer_schemas.create_task),
    retrieve=extend_schema(**serializer_schemas.detail_task),
    update=extend_schema(**serializer_schemas.update_task),
    destroy=extend_schema(**serializer_schemas.delete_task),
)
class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    List, create, retrieve, update and delete tasks.
    """

    queryset = TaskModel.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthenticated, IsTaskCreatorOrAssignee)
    pagination_class = TaskPagination

    http_method_names = ("get", "post", "put", "delete")

    def get_queryset(self):
        return self.queryset.filter(
            Q(creator=self.request.user) | Q(assignee=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @extend_schema(**serializer_schemas.set_task_status)
    @action(
        detail=True,
        methods=["put"],
        url_path="status",
        url_name="status",
        serializer_class=TaskStatusSerializer,
    )
    def set_status(self, request, pk=None):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=["Comments"])
@extend_schema_view(
    list=extend_schema(**serializer_schemas.list_comment),
    create=extend_schema(**serializer_schemas.create_comment),
    update=extend_schema(**serializer_schemas.update_comment),
    destroy=extend_schema(**serializer_schemas.delete_comment),
)
class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    List, create, update and delete comments.
    """

    queryset = CommentModel.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated, IsCommentAuthorOrReadOnly)
    pagination_class = CommentPagination

    http_method_names = ("get", "post", "put", "delete")

    def get_queryset(self):
        queryset = self.queryset.filter(
            Q(task__creator=self.request.user) | Q(task__assignee=self.request.user)
        )
        if self.action == "list":
            filters = CommentFilterSerializer(data=self.request.query_params.dict())
            filters.is_valid(raise_exception=True)
            task_id = filters.validated_data.get("task")
            if task_id is not None:
                queryset = queryset.filter(task_id=task_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
