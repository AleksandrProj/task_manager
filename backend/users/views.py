from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users import schemas
from users.serializers import (
    CurrentUserSerializer,
    TokenRefreshSerializer,
    UserSerializer,
)


class UserPagination(PageNumberPagination):
    page_size = 20


@extend_schema(tags=["Users"])
@extend_schema_view(list=extend_schema(**schemas.list_users))
class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = get_user_model().objects.filter(is_active=True).order_by("id")
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = UserPagination
    http_method_names = ("get", "head", "options")

    @extend_schema(**schemas.current_user)
    @action(detail=False, methods=["get"], serializer_class=CurrentUserSerializer)
    def me(self, request):
        return Response(self.get_serializer(request.user).data)


@extend_schema(**schemas.login)
class LoginView(TokenObtainPairView):
    """Authenticate an existing Django user with username and password."""


@extend_schema(**schemas.refresh)
class RefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer
