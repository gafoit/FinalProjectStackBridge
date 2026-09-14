from django.contrib import admin
from django.db.models import Count

from .models import Membership, Roles, Team


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ('profile', 'role')
    autocomplete_fields = ('profile',)
    verbose_name = 'Участник'
    verbose_name_plural = 'Участники'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'members_count', 'invite_code')
    search_fields = ('name', 'owner__user__username', 'owner__user__email')
    list_select_related = ('owner',)
    autocomplete_fields = ('owner',)
    readonly_fields = ('invite_code',)
    inlines = (MembershipInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_members_count=Count('memberships'))

    @admin.display(description='Участников', ordering='_members_count')
    def members_count(self, obj):
        return obj._members_count


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'profile', 'role')
    list_filter = ('role',)
    search_fields = ('team__name', 'profile__user__username', 'profile__user__email')
    list_select_related = ('team', 'profile', 'profile__user')
    autocomplete_fields = ('team', 'profile')
    ordering = ('team_id', 'profile_id')
    list_per_page = 50

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['choices'] = Roles.choices
        return super().formfield_for_choice_field(db_field, request, **kwargs)
