from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TaskModel(models.Model):
    """A task with an author and an optional assignee."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField("Title", max_length=150)
    description = models.CharField("Description", max_length=500, blank=True)
    status = models.CharField(
        "Status",
        max_length=12,
        choices=Status,
        default=Status.NEW,
    )
    priority = models.CharField(
        "Priority",
        max_length=6,
        choices=Priority,
        default=Priority.LOW,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Creator",
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Assignee",
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(assignee__isnull=True)
                    | ~models.Q(assignee=models.F("creator"))
                ),
                name="task_assignee_not_creator",
            ),
        )

    def clean(self):
        super().clean()
        if self.assignee_id is not None and self.assignee_id == self.creator_id:
            raise ValidationError(
                {"assignee": "The task creator cannot be its assignee."}
            )

    def __str__(self):
        return self.title


class CommentModel(models.Model):
    """A user's comment on a task."""

    text = models.CharField("Text comment", max_length=500)
    task = models.ForeignKey(
        TaskModel,
        verbose_name="Comment for task",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Author comment",
        on_delete=models.PROTECT,
        related_name="task_comments",
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    class Meta:
        ordering = ("created_at", "pk")
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return self.text[:50]
