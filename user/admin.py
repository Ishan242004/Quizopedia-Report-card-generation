from django.contrib import admin
from .models import Student, ProfileUpdateRequest, Subject, Question

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_name', 'get_email', 'phone', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__email')

    def get_username(self, obj):
        return obj.user.username if obj.user else ""
    get_username.short_description = 'Username'

    def get_name(self, obj):
        return obj.user.first_name if obj.user else ""
    get_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.user.email if obj.user else ""
    get_email.short_description = 'Email'


@admin.register(ProfileUpdateRequest)
class ProfileUpdateRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__user__username', 'name', 'email', 'phone')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'question_text')
    list_filter = ('subject',)
    search_fields = ('question_text',)


