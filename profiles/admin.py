from django.contrib import admin

from profiles.models import Profile

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_select_related = ('user',)
    autocomplete_fields = ('user',)

    @admin.display(description='Имя')
    def full_name(self, obj):
        return obj.user.get_full_name() or '—'

    @admin.display(description='Email')
    def email(self, obj):
        return obj.user.email