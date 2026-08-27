from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/students/', views.student_list, name='admin_students'),
    path('admin-dashboard/approvals/', views.profile_approvals, name='admin_profile_approvals'),
    path('admin-dashboard/profile/', views.admin_profile, name='admin_profile'),
    path('questions/', views.question_list, name='question_list'),
    path('questions/add/', views.question_add, name='question_add'),
    path('questions/edit/<int:pk>/', views.question_edit, name='question_edit'),
    path('questions/delete/<int:pk>/', views.question_delete, name='question_delete'),
    path('questions/subject/<int:pk>/', views.subject_questions, name='subject_questions'),
    path('questions/view/<int:pk>/', views.question_detail, name='question_detail'),
    path('admin-dashboard/report-cards/', views.admin_report_cards, name='admin_report_cards'),
    path('admin-dashboard/report-card/<int:pk>/', views.admin_report_card_detail, name='admin_report_card_detail'),
    path('admin-dashboard/report-card/<int:pk>/delete/', views.admin_report_card_delete, name='admin_report_card_delete'),
]
