from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/students/', views.student_list, name='admin_students'),
    path('admin-dashboard/profile/', views.admin_profile, name='admin_profile'),
]
