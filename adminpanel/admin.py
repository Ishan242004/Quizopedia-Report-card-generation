from django.contrib import admin
from .models import Admin

@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_email', 'phone', 'user')
    search_fields = ('user__username', 'user__email')

    def get_username(self, obj):
        return obj.user.username if obj.user else ""
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email if obj.user else ""
    get_email.short_description = 'Email'
