from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/attempt/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('results/', views.result_list, name='result_list'),
    path('results/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('report-card/', views.report_card_view, name='report_card'),
]