from django.db import models


# Create your models here.

class TaskStatus(models.TextChoices):
    OPEN = 'open', 'Создана'
    IN_PROGRESS = 'in_progress', 'В процессе'
    DONE = 'done', 'Выполнена'
    # canceled = 'canceled', 'Отменена'


class Task(models.Model):
    title = models.CharField(max_length=100, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    team = models.ForeignKey(
        'teams.Team',
        related_name='tasks',
        on_delete=models.CASCADE,
        verbose_name='Команда',
    )
    created_by = models.ForeignKey(
        'profiles.Profile',
        related_name='created_tasks',
        on_delete=models.CASCADE,
        verbose_name='Создал',
    )
    assignee = models.ForeignKey(
        'profiles.Profile',
        related_name='assigned_tasks',
        on_delete=models.CASCADE,
        verbose_name='Исполнитель',
    )
    due_date = models.DateTimeField(verbose_name='Срок')
    status = models.CharField(
        choices=TaskStatus.choices,
        max_length=15,
        default=TaskStatus.OPEN,
        verbose_name='Статус',
    )

    def __str__(self):
        return f"{self.title}: {self.assignee} до {self.due_date}"

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['title', 'due_date']


class TaskComment(models.Model):
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        'profiles.Profile',
        related_name='task_comments',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    task = models.ForeignKey(
        'Task',
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Задача',
    )

    def __str__(self):
        return f"[{self.task}] {self.author}: {self.text}"

    class Meta:
        verbose_name = 'Комментарий к задаче'
        verbose_name_plural = 'Комментарии к задачам'


class TaskRating(models.Model):
    task = models.ForeignKey(
        'Task', on_delete=models.CASCADE, related_name='ratings', verbose_name='Задача',
    )
    author = models.ForeignKey(
        'profiles.Profile',
        related_name='given_ratings',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    score = models.PositiveSmallIntegerField(verbose_name='Оценка')
    score_comment = models.TextField(verbose_name='Комментарий к оценке')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Поставлена')

    class Meta:
        verbose_name = 'Оценка задачи'
        verbose_name_plural = 'Оценки задач'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(score__gte=1, score__lte=5),
                name='score_between_1_and_5',
            ),
            models.UniqueConstraint(
                fields=['task', 'author'],
                name='one_rating_per_manager_per_task',
            ),
        ]

    def __str__(self):
        return f"{self.task.title}: {self.score}"
