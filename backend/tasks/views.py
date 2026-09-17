from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import CommentModel, TaskModel
from tasks.permissions import IsCommentAuthorOrReadOnly, IsTaskCreatorOrAssignee
from tasks.schemas import serializer_schemas
from tasks.serializers import CommentSerializer, TasksSerializer, TaskStatusSerializer


class TaskPagination(PageNumberPagination):
    """
    Pagination for tasks
    """

    page_size = 20


class CommentPagination(PageNumberPagination):
    """
    Pagination for comments
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
        return self.queryset.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
