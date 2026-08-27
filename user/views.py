from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Student, ProfileUpdateRequest, Subject, Question, ReportCard
from .decorators import student_required
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Avg

def home_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    return redirect('login')

def register(request):
    errors = []
    student = None

    if request.method == 'GET' and request.GET.get('unregistered') == '1':
        errors.append("You have not registered. Please register first.")

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
            # Handle email/username login by resolving to the correct username (case-insensitive)
            auth_username = username_or_email
            user_exists = False
            
            if '@' in username_or_email:
                user_by_email = User.objects.filter(email__iexact=username_or_email).first()
                if user_by_email:
                    auth_username = user_by_email.username
                    user_exists = True
            else:
                user_by_username = User.objects.filter(username__iexact=username_or_email).first()
                if user_by_username:
                    auth_username = user_by_username.username
                    user_exists = True
            
            if not user_exists:
                return redirect('/register/?unregistered=1')
                
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
    
    # Calculate statistics
    completed_quizzes = student.report_cards.count() if student else 0
    avg_score = student.report_cards.aggregate(Avg('percentage'))['percentage__avg'] if student else None
    avg_score_formatted = f"{round(avg_score, 1)}%" if avg_score is not None else "0%"
    
    # Retrieve available quizzes (subjects) with question counts
    available_subjects = []
    for s in Subject.objects.filter(questions__isnull=False).distinct():
        # Sum up individual questions in this subject's Question records
        total_q = sum(
            len([line.strip() for line in q.question_text.split('\n') if line.strip()])
            for q in s.questions.all()
        )
        available_subjects.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'total_questions': total_q
        })
        
    # Get recent progress / report cards for this student
    recent_progress = []
    if student:
        recent_progress = student.report_cards.all().order_by('-created_at')
        
    context = {
        'student': student,
        'user': request.user,
        'completed_quizzes': completed_quizzes,
        'avg_score': avg_score_formatted,
        'subjects_count': Subject.objects.filter(questions__isnull=False).distinct().count(),
        'available_subjects': available_subjects,
        'recent_progress': recent_progress,
    }
    return render(request, 'dashboard.html', context)

@student_required
def profile_view(request):
    errors = []
    success_msg = None
    student = getattr(request.user, 'student', None)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        
        if not name or not email or not phone:
            errors.append("Name, Email, and Phone are required.")
        else:
            # Validate email
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Enter a valid email address.")
                
            # Validate phone
            if not re.match(r'^[\d\s\-\+\(\)]{7,20}$', phone):
                errors.append("Enter a valid phone number.")
                
            # Email uniqueness check
            if not errors:
                if User.objects.exclude(id=request.user.id).filter(email__iexact=email).exists():
                    errors.append("Email already in use.")
            
            if not errors:
                password_updated = False
                if password:
                    request.user.set_password(password)
                    request.user.save()
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, request.user)
                    password_updated = True
                    success_msg = "Password updated successfully. "
                
                # Check for changes in profile fields
                is_changed = (
                    name != request.user.first_name or
                    email != request.user.email or
                    phone != student.phone
                )
                
                if is_changed:
                    # Get or create pending update request
                    update_req, created = ProfileUpdateRequest.objects.get_or_create(
                        student=student,
                        status='pending',
                        defaults={'name': name, 'email': email, 'phone': phone}
                    )
                    if not created:
                        update_req.name = name
                        update_req.email = email
                        update_req.phone = phone
                        update_req.save()
                    
                    req_msg = "Profile update submitted successfully. Pending Admin Approval."
                    success_msg = (success_msg + req_msg) if success_msg else req_msg
                else:
                    if not password_updated:
                        success_msg = "No changes were made."
                        
    # Fetch latest update request to show status and pre-populate form
    latest_request = None
    if student:
        latest_request = student.profile_updates.order_by('-updated_at').first()
        
    form_name = request.user.first_name
    form_email = request.user.email
    form_phone = student.phone if student else ''
    
    if latest_request and latest_request.status == 'pending':
        form_name = latest_request.name
        form_email = latest_request.email
        form_phone = latest_request.phone
        
    return render(request, 'profile.html', {
        'student': student,
        'user': request.user,
        'errors': errors,
        'success': success_msg,
        'latest_request': latest_request,
        'form_name': form_name,
        'form_email': form_email,
        'form_phone': form_phone,
    })
@student_required
def quiz_attempt(request, subject_id):
    student = get_object_or_404(Student, user=request.user)
    subject = get_object_or_404(Subject, id=subject_id)
    questions = Question.objects.filter(subject=subject).order_by('id')
    
    if request.method == 'POST':
        attempted_count = 0
        correct_count = 0
        
        for q in questions:
            ans_key = f"question_{q.id}"
            selected_option = request.POST.get(ans_key, '').strip()
            
            if selected_option:
                attempted_count += 1
                if selected_option == q.correct_option:
                    correct_count += 1
                    
        total_questions = questions.count()
        wrong_answers = total_questions - correct_count
        total_marks = total_questions * 10
        obtained_marks = correct_count * 10
        percentage = round((obtained_marks / total_marks) * 100, 1) if total_questions > 0 else 0.0
        
        # Calculate grade
        if percentage >= 90:
            grade = 'A'
        elif percentage >= 80:
            grade = 'B'
        elif percentage >= 70:
            grade = 'C'
        elif percentage >= 60:
            grade = 'D'
        else:
            grade = 'F'
            
        # Create the ReportCard record
        report_card = ReportCard.objects.create(
            student=student,
            subject=subject,
            total_questions=total_questions,
            attempted_questions=attempted_count,
            correct_answers=correct_count,
            wrong_answers=wrong_answers,
            total_marks=total_marks,
            obtained_marks=obtained_marks,
            percentage=percentage,
            result_grade=grade
        )
        
        messages.success(request, f"Quiz submitted successfully! Your score: {percentage}% ({grade})")
        return redirect('report_card_view', pk=report_card.id)
        
    return render(request, 'quiz_attempt.html', {
        'student': student,
        'subject': subject,
        'questions': questions,
        'total_questions': questions.count(),
    })

def grade_descriptive_answer(question_text, student_answer):
    answer_clean = student_answer.strip().lower()
    if len(answer_clean) < 15:
        return False
        
    question_clean = question_text.strip().lower()
    
    # Key vocabulary words associated with Python, programming, and OOP
    generic_keywords = [
        'def', 'return', 'class', 'python', 'function', 'object', 'variable', 
        'loop', 'import', 'code', 'pillar', 'oops', 'inheritance', 'polymorphism', 
        'encapsulation', 'abstraction', 'init', 'self', 'arguments', 'parameters',
        'instance', 'methods', 'conditional', 'list', 'dict', 'set', 'tuple'
    ]
    
    # Check if answer contains generic programming keywords
    for keyword in generic_keywords:
        if keyword in answer_clean:
            return True
            
    # Check if we match significant words from the question text itself
    question_words = [w for w in re.split(r'\W+', question_clean) if len(w) > 3]
    match_count = sum(1 for w in question_words if w in answer_clean)
    if match_count >= 1:
        return True
        
    return False

@student_required
def report_card_view(request, pk):
    student = get_object_or_404(Student, user=request.user)
    report_card = get_object_or_404(ReportCard, id=pk, student=student)
    return render(request, 'report_card.html', {
        'student': student,
        'report_card': report_card,
    })
