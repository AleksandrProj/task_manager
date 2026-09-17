from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsTaskCreatorOrReadOnly(BasePermission):
    """
    Allow authenticated readers and restrict changes to the task creator.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.creator_id == request.user.pk


class IsCommentAuthorOrReadOnly(BasePermission):
    """
    Allow authenticated readers and restrict changes to the comment author.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author_id == request.user.pk
