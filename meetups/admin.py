from django.contrib import admin

from .models import Meetup


@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'organizer', 'starts_at', 'ends_at', 'is_cancelled')
    list_filter = ('is_cancelled', 'team')
    search_fields = ('title', 'description', 'team__name', 'organizer__user__username')
    autocomplete_fields = ('team', 'organizer')
    list_select_related = ('team', 'organizer', 'organizer__user')
    filter_horizontal = ('participants',)
    date_hierarchy = 'starts_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'is_cancelled')}),
        ('Связи', {'fields': ('team', 'organizer', 'participants')}),
        ('Время', {'fields': ('starts_at', 'ends_at')}),
        ('Служебное', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
