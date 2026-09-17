from rest_framework import routers

from tasks.views import CommentViewSet, TaskViewSet
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"users", UserViewSet, basename="user")
