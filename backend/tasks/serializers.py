from django.contrib.auth import get_user_model
from rest_framework import serializers

from tasks.models import CommentModel, TaskModel


class TasksSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks
    """

    assignee = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TaskModel
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "creator",
            "assignee",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "creator", "created_at", "updated_at")

    def validate_assignee(self, assignee):
        creator_id = (
            self.instance.creator_id
            if self.instance is not None
            else self.context["request"].user.pk
        )
        if assignee is not None and assignee.pk == creator_id:
            raise serializers.ValidationError(
                "The task creator cannot be its assignee."
            )
        return assignee


class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=TaskModel.Status.choices)

    def validate(self, attrs):
        if set(self.initial_data) - {"status"}:
            raise serializers.ValidationError("Only the status field is allowed.")
        return attrs

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.save(update_fields=("status", "updated_at"))
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments
    """

    class Meta:
        model = CommentModel
        fields = (
            "id",
            "text",
            "task",
            "author",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")
