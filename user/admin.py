from django.contrib import admin
from .models import Student, ProfileUpdateRequest

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_email', 'phone', 'user')
    search_fields = ('user__username', 'user__email')

    def get_username(self, obj):
        return obj.user.username if obj.user else ""
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email if obj.user else ""
    get_email.short_description = 'Email'


@admin.register(ProfileUpdateRequest)
class ProfileUpdateRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__user__username', 'name', 'email', 'phone')


