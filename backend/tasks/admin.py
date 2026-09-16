from django.contrib import admin

from tasks.models import CommentModel, TasksModel

admin.site.register(TasksModel)
admin.site.register(CommentModel)
