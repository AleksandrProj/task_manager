from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsTaskCreatorOrAssignee(BasePermission):
    """Allow creators to edit tasks and assignees to use the status action."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or obj.creator_id == request.user.pk:
            return True
        return view.action == "set_status" and obj.assignee_id == request.user.pk


class IsCommentAuthorOrReadOnly(BasePermission):
    """
    Allow authenticated readers and restrict changes to the comment author.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author_id == request.user.pk
