"""Shared OpenAPI responses. These serializers only describe documentation."""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers


class TokenErrorMessageSerializer(serializers.Serializer):
    token_class = serializers.CharField()
    token_type = serializers.CharField()
    message = serializers.CharField()


class ApiErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField(required=False)
    messages = TokenErrorMessageSerializer(many=True, required=False)


def example_response(serializer, value, description):
    return OpenApiResponse(
        response=serializer,
        description=description,
        examples=[OpenApiExample("Example", value=value)],
    )


ERROR_RESPONSES = {
    400: example_response(
        {
            "oneOf": [
                {
                    "type": "object",
                    "minProperties": 1,
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                    "additionalProperties": False,
                },
            ]
        },
        {"non_field_errors": ["Invalid data. Expected a dictionary, but got list."]},
        "Validation errors are lists of messages keyed by field name, including "
        "non_field_errors. Malformed JSON returns a detail message.",
    ),
    401: OpenApiResponse(
        response=ApiErrorSerializer,
        description="Authentication is missing or invalid. The token may be expired "
        "or the user inactive/deleted. Use an access token with the Bearer prefix.",
        examples=[
            OpenApiExample(
                "No credentials",
                value={"detail": "Authentication credentials were not provided."},
            ),
            OpenApiExample(
                "Expired access token",
                value={
                    "detail": "Given token not valid for any token type",
                    "code": "token_not_valid",
                    "messages": [
                        {
                            "token_class": "AccessToken",
                            "token_type": "access",
                            "message": "Token is expired",
                        }
                    ],
                },
            ),
        ],
    ),
    403: example_response(
        ApiErrorSerializer,
        {"detail": "You do not have permission to perform this action."},
        "The authenticated user is not allowed to perform this action, or a "
        "session-authenticated write request failed CSRF validation.",
    ),
    404: example_response(
        ApiErrorSerializer,
        {"detail": "Not found."},
        "The object does not exist, is hidden from the current user, or the "
        "requested page does not exist.",
    ),
}


def error_responses(*codes):
    return {code: ERROR_RESPONSES[code] for code in codes}
