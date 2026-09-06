from django.contrib import admin

from tasks.models import Task, TaskRating
from tasks.models import TaskComment

# Register your models here.


admin.site.register(Task)
admin.site.register(TaskComment)
admin.site.register(TaskRating)
