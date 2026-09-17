from django.contrib import admin

from tasks.models import CommentModel, TaskModel

admin.site.register(TaskModel)
admin.site.register(CommentModel)
