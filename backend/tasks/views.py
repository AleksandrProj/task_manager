from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from tasks.models import TasksModel
from tasks.permissions import IsTaskCreatorOrReadOnly
from tasks.schemas import serializer_schemas
from tasks.serializers import TasksSerializer


class TaskPagination(PageNumberPagination):
    page_size = 20

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

    queryset = TasksModel.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthenticated, IsTaskCreatorOrReadOnly)
    pagination_class = TaskPagination

    http_method_names = ["get", "post", "put", "delete"]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
