from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Student, Quiz, Question, StudentAttempt, ReportCard
from .decorators import student_required

def home_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    return redirect('login')

def register(request):
    errors = []
    student = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        terms = request.POST.get('terms')

        # Perform server-side validation to match project requirement tests
        if not terms or terms != 'on':
            errors.append('You must agree to the Terms & Conditions.')
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        # Database unique checks (only run if no basic validation errors)
        if not errors:
            if User.objects.filter(username=username).exists():
                errors.append('Username already exists.')
            if User.objects.filter(email=email).exists():
                errors.append('Email already exists.')

        if not errors:
            # Create Django User (hashes password automatically)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            # Create Student Profile
            student = Student.objects.create(
                user=user,
                phone=phone
            )

    return render(request, 'register.html', {
        'errors': errors,
        'student': student
    })

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')
        
    errors = []
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username_or_email or not password:
            errors.append("Username/Email and password are required.")
        else:
            # Handle email login by looking up the username associated with the email
            auth_username = username_or_email
            if '@' in username_or_email:
                try:
                    user_by_email = User.objects.get(email=username_or_email)
                    auth_username = user_by_email.username
                except User.DoesNotExist:
                    pass
            
            user = authenticate(request, username=auth_username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            else:
                errors.append("Invalid username or password.")
                
    return render(request, 'login.html', {'errors': errors})

def logout_view(request):
    logout(request)
    return redirect('login')

@student_required
def dashboard(request):
    student = getattr(request.user, 'student', None)
    context = {
        'student': student,
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)

@student_required
def quiz_list(request):
    quizzes = Quiz.objects.all()
    student = getattr(request.user, 'student', None)
    context = {
        'quizzes': quizzes,
        'student': student,
    }
    return render(request, 'quiz_list.html', context)

@student_required
def result_list(request):
    student = getattr(request.user, 'student', None)
    attempts = StudentAttempt.objects.filter(student=student) if student else []
    context = {
        'attempts': attempts,
        'student': student,
    }
    return render(request, 'result_list.html', context)

@student_required
def report_card_view(request):
    student = getattr(request.user, 'student', None)
    report_cards = ReportCard.objects.filter(student=student) if student else []
    context = {
        'report_cards': report_cards,
        'student': student,
    }
    return render(request, 'report_card.html', context)

@student_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    student = getattr(request.user, 'student', None)
    context = {
        'quiz': quiz,
        'questions': questions,
        'student': student,
    }
    return render(request, 'take_quiz.html', context)

@student_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    student = getattr(request.user, 'student', None)
    
    if request.method == 'POST':
        questions = quiz.questions.all()
        score = 0
        
        for question in questions:
            selected_option = request.POST.get(f'question_{question.id}')
            if selected_option == question.correct_option:
                score += question.marks
                
        # Create StudentAttempt
        attempt = StudentAttempt.objects.create(
            student=student,
            quiz=quiz,
            score=score
        )
        
        # Calculate grade and remarks
        percentage = (score / quiz.total_marks) * 100 if quiz.total_marks > 0 else 0
        if percentage >= 90:
            grade = 'A'
            remarks = "Outstanding performance!"
        elif percentage >= 80:
            grade = 'B'
            remarks = "Great job! Keep it up."
        elif percentage >= 70:
            grade = 'C'
            remarks = "Good performance, but room for improvement."
        elif percentage >= 60:
            grade = 'D'
            remarks = "Passed. Needs more practice."
        else:
            grade = 'F'
            remarks = "Needs significant improvement."
            
        # Create ReportCard
        ReportCard.objects.create(
            student=student,
            attempt=attempt,
            grade=grade,
            remarks=remarks
        )
        
        return redirect('quiz_result', attempt_id=attempt.id)
        
    return redirect('quiz_list')

@student_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(StudentAttempt, id=attempt_id, student=request.user.student)
    report_card = getattr(attempt, 'report_card', None)
    percentage = (attempt.score / attempt.quiz.total_marks) * 100 if attempt.quiz.total_marks > 0 else 0
    student = getattr(request.user, 'student', None)
    context = {
        'attempt': attempt,
        'report_card': report_card,
        'percentage': percentage,
        'student': student,
    }
    return render(request, 'quiz_result.html', context)
