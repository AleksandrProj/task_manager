from rest_framework import routers

from tasks.views import TaskViewSet

router = routers.DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
