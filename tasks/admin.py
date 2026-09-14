from django.contrib import admin

from .models import Task, TaskComment, TaskRating


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    fields = ('author', 'text', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('author',)


class TaskRatingInline(admin.TabularInline):
    model = TaskRating
    extra = 0
    fields = ('author', 'score', 'score_comment', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('author',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'assignee', 'status', 'due_date')
    list_filter = ('status', 'team')
    search_fields = ('title', 'description')
    autocomplete_fields = ('team', 'created_by', 'assignee')
    list_select_related = ('team', 'created_by', 'assignee', 'assignee__user')
    date_hierarchy = 'due_date'
    inlines = (TaskCommentInline, TaskRatingInline)
    fieldsets = (
        (None, {'fields': ('title', 'description', 'status')}),
        ('Связи', {'fields': ('team', 'created_by', 'assignee')}),
        ('Сроки', {'fields': ('due_date',)}),
    )


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    search_fields = ('text', 'task__title', 'author__user__username')
    list_select_related = ('task', 'author', 'author__user')
    autocomplete_fields = ('task', 'author')
    readonly_fields = ('created_at',)


@admin.register(TaskRating)
class TaskRatingAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('task__title', 'author__user__username', 'score_comment')
    list_select_related = ('task', 'author', 'author__user')
    autocomplete_fields = ('task', 'author')
    readonly_fields = ('created_at',)
