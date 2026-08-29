from django.utils import timezone

from django.db import models


# Create your models here.

class TaskStatus(models.TextChoices):
    OPEN = 'open', 'Создана'
    IN_PROGRESS = 'in_progress', 'В процессе'
    DONE = 'done', 'Выполнена'
    # canceled = 'canceled', 'Отменена'


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    # Должна знать команду, так как задания относятся к ней.
    team = models.ForeignKey(
        "teams.Team",
        related_name='tasks',
        on_delete=models.CASCADE,
    )
    # Храним также тех кто их создал
    created_by = models.ForeignKey(
        'profiles.Profile',
        related_name='created_tasks',
        on_delete=models.CASCADE,
    )
    # И кому назначили
    assignee = models.ForeignKey(
        'profiles.Profile',
        related_name='assigned_tasks',
        on_delete=models.CASCADE,
    )
    # Дату назначения
    due_date = models.DateTimeField()
    status = models.CharField(choices=TaskStatus.choices, max_length=15, default=TaskStatus.OPEN)

    def __str__(self):
        return f"{self.title}: {self.assignee} до {self.due_date}"

    class Meta:
        ordering = ['title', 'due_date']


class TaskComment(models.Model):
    text = models.TextField()
    author = models.ForeignKey('profiles.Profile',
                               related_name='task_comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey('Task', related_name='comments', on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.task}] {self.author}: {self.text}"


class TaskRating(models.Model):
    # Задача
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='ratings')
    # Автор оценки
    author = models.ForeignKey(
        'profiles.Profile',
        related_name='given_ratings',
        on_delete=models.CASCADE,
    )
    # Оценка
    score = models.PositiveSmallIntegerField()
    # Комментарий к оценке
    score_comment = models.TextField()
    # Когда поставили оценку
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Оценка от 1 до 5
            models.CheckConstraint(
                condition=models.Q(score__gte=1, score__lte=5),
                name='score_between_1_and_5',
            ),
            # Только одна оценка на задачу от одного менеджера
            models.UniqueConstraint(
                fields=['task', 'author'],
                name='one_rating_per_manager_per_task',
            ),
        ]

    def __str__(self):
        return f"{self.task.title}: {self.score}"
