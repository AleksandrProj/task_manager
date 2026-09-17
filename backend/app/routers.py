from rest_framework import routers

from tasks.views import CommentViewSet, TaskViewSet

router = routers.DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", CommentViewSet, basename="comment")
