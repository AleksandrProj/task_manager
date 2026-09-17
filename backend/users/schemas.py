from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers

from app.schemas import ApiErrorSerializer, error_responses, example_response
from users.serializers import CurrentUserSerializer, UserSerializer


class TokenPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


list_users = {
    "summary": "List active users",
    "description": "Active users including the current user, ordered by ID. "
    "Only public id and username fields are returned. 20 users per page. "
    "A task creator still cannot be selected as that task's assignee.",
    "responses": {
        200: example_response(
            UserSerializer, {"id": 2, "username": "alex"}, "Paginated active users."
        ),
        **error_responses(401, 404),
    },
}

current_user = {
    "summary": "Get current user",
    "description": "The authenticated user's own profile, without pagination. "
    "No passwords or administrative fields are exposed. This API is read-only.",
    "responses": {
        200: example_response(
            CurrentUserSerializer,
            {
                "id": 2,
                "username": "alex",
                "email": "alex@example.com",
                "first_name": "Alex",
                "last_name": "Tester",
            },
            "Current user's profile.",
        ),
        **error_responses(401),
    },
}

login = {
    "tags": ["Authentication"],
    "summary": "Obtain access and refresh tokens",
    "description": "Use an existing active Django account. No prior authorization "
    "is required. Access expires in 15 minutes, refresh in one day. "
    "For protected requests send Authorization: Bearer <access>. In Swagger, "
    "paste the access token into Authorize / jwtAuth without the Bearer prefix. "
    "Example credentials and tokens are placeholders, not a working account.",
    "examples": [
        OpenApiExample(
            "Login credentials",
            value={
                "username": "your_username",
                "password": "your_password",
            },
            request_only=True,
        )
    ],
    "responses": {
        200: example_response(
            TokenPairResponseSerializer,
            {
                "access": "<access-token>",
                "refresh": "<refresh-token>",
            },
            "Token pair. Replace placeholders with the actual response values.",
        ),
        **error_responses(400),
        401: example_response(
            ApiErrorSerializer,
            {"detail": "No active account found with the given credentials"},
            "Incorrect username/password or inactive account.",
        ),
    },
}

refresh = {
    "tags": ["Authentication"],
    "summary": "Refresh access token",
    "description": "Submit a valid refresh token from the login response. No access "
    "token is required. Returns only a new access token; refresh is not rotated "
    "and its original expiry does not change. Log in again after refresh expires.",
    "examples": [
        OpenApiExample(
            "Refresh token",
            value={"refresh": "<refresh-token-from-login>"},
            request_only=True,
        )
    ],
    "responses": {
        200: example_response(
            AccessTokenResponseSerializer,
            {"access": "<new-access-token>"},
            "New access token, valid for 15 minutes.",
        ),
        **error_responses(400),
        401: example_response(
            ApiErrorSerializer,
            {"detail": "Token is expired", "code": "token_not_valid"},
            "Expired, invalid or wrong-type token; "
            "the user may also be inactive/deleted.",
        ),
    },
}
