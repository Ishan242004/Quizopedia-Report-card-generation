from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/students/', views.student_list, name='admin_students'),
    path('admin-dashboard/quizzes/', views.quiz_list, name='admin_quizzes'),
    path('admin-dashboard/questions/', views.question_list, name='admin_questions'),
    path('admin-dashboard/attempts/', views.attempt_list, name='admin_attempts'),
    path('admin-dashboard/report-cards/', views.report_card_list, name='admin_report_cards'),
]
