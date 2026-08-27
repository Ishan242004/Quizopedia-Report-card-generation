from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('quiz/<int:subject_id>/', views.quiz_attempt, name='quiz_attempt'),
    path('report-card/<int:pk>/', views.report_card_view, name='report_card_view'),
]