from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from tasks.models import CommentModel, TaskModel
from tasks.permissions import IsCommentAuthorOrReadOnly, IsTaskCreatorOrReadOnly
from tasks.schemas import serializer_schemas
from tasks.serializers import CommentSerializer, TasksSerializer


class TaskPagination(PageNumberPagination):
    page_size = 20


class CommentPagination(PageNumberPagination):
    page_size = 10


@extend_schema(tags=["Tasks"])
@extend_schema_view(
    list=extend_schema(**serializer_schemas.list_task),
    create=extend_schema(**serializer_schemas.create_task),
    retrieve=extend_schema(**serializer_schemas.detail_task),
    update=extend_schema(**serializer_schemas.update_task),
    destroy=extend_schema(**serializer_schemas.delete_task),
)
class TaskViewSet(ModelViewSet):
    """
    List, create, retrieve, update and delete tasks.
    """

    queryset = TaskModel.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthenticated, IsTaskCreatorOrReadOnly)
    pagination_class = TaskPagination

    http_method_names = ("get", "post", "put", "delete")

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
