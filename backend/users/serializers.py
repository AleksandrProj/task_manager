from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer as SimpleJWTTokenRefreshSerializer,
)


class UserSerializer(serializers.ModelSerializer):
    """Public fields for choosing an assignee."""

    class Meta:
        model = get_user_model()
        fields = ("id", "username")
        read_only_fields = fields


class CurrentUserSerializer(serializers.ModelSerializer):
    """The authenticated user's own profile."""

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = fields


class TokenRefreshSerializer(SimpleJWTTokenRefreshSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except get_user_model().DoesNotExist as exc:
            # SimpleJWT 5.5.1 doesn't handle users deleted after token issuance.
            raise AuthenticationFailed(
                "No active account found for the token."
            ) from exc
