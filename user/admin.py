from django.contrib import admin
from .models import Student, Quiz, Question, StudentAttempt, ReportCard

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

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'total_marks')
    search_fields = ('title',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'correct_option', 'marks')
    list_filter = ('quiz',)
    search_fields = ('text',)

@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'completed_at')
    list_filter = ('quiz', 'completed_at')
    search_fields = ('student__username', 'quiz__title')

@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student', 'grade', 'generated_at')
    search_fields = ('student__username', 'grade')
