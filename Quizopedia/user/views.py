from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import Student, ProfileUpdateRequest, Subject, Question, ReportCard, StudentOTP, ReportCardAnswer
from .decorators import student_required
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Avg, Q
from django.core.paginator import Paginator

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

def mask_email(email):
    """Utility to mask email address for privacy in verification displays (e.g. j***e@example.com)."""
    if not email or '@' not in email:
        return email or ''
    parts = email.split('@', 1)
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + '*'
    else:
        masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"


def send_student_otp(request, user, student):
    """
    Helper to generate a secure 6-digit OTP, invalidate previous unused OTPs,
    save the new StudentOTP record with expiry, and send it via Django's email backend.
    Returns (success: bool, error_msg: str | None).
    """
    student_email = user.email or getattr(student, 'email', '')
    if not student_email:
        return False, "Your account does not have a registered email address. Please contact an administrator."

    otp_expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    otp_code = StudentOTP.generate_otp_code()
    expires_at = timezone.now() + timedelta(minutes=otp_expiry_minutes)

    with transaction.atomic():
        # Invalidate previous unused OTPs for this student
        StudentOTP.objects.filter(student=student, is_used=False).update(is_used=True)
        # Create new OTP record
        otp_record = StudentOTP.objects.create(
            student=student,
            otp=otp_code,
            expires_at=expires_at,
            is_used=False
        )

    # Print OTP prominently to the terminal console for instant access
    print("\n" + "=" * 55, flush=True)
    print(f"🔑 [QUIZOPEDIA OTP] For: {user.username} ({student_email})", flush=True)
    print(f"👉 YOUR OTP CODE: >>> {otp_code} <<<", flush=True)
    print(f"⏰ Valid for: {otp_expiry_minutes} minutes", flush=True)
    print("=" * 55 + "\n", flush=True)

    # Email message preparation
    subject = "Quizopedia Login Verification Code"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"Your one-time login verification code (OTP) for Quizopedia is:\n\n"
        f"    {otp_code}\n\n"
        f"This code is valid for {otp_expiry_minutes} minutes and can only be used once.\n\n"
        f"If you did not attempt to sign in to Quizopedia, please ignore this email or secure your account.\n\n"
        f"Best regards,\nQuizopedia Learning Platform"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
            fail_silently=False,
        )
        return True, None
    except Exception as e:
        # Delete the generated OTP record upon email delivery failure to prevent dangling codes
        otp_record.delete()
        return False, "Unable to send verification code due to an email delivery error. Please try again later."


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
                # If staff/admin user, direct login without student OTP
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    return redirect('admin_dashboard')

                # For student users: initiate secure OTP verification flow
                student = getattr(user, 'student', None)
                if not student:
                    student = Student.objects.create(user=user, phone='')

                success, err = send_student_otp(request, user, student)
                if success:
                    request.session['pre_otp_user_id'] = user.id
                    request.session['otp_attempts'] = 0
                    request.session['otp_resend_count'] = 0
                    request.session['otp_last_sent'] = timezone.now().timestamp()
                    messages.success(request, f"A 6-digit verification code has been sent to your registered email.")
                    return redirect('verify_otp')
                else:
                    errors.append(err)
            else:
                errors.append("Invalid username or password.")
                
    return render(request, 'login.html', {'errors': errors})


def verify_otp_view(request):
    """
    Renders the OTP verification form and validates the submitted 6-digit OTP.
    Upon successful validation, logs in the student and redirects to the dashboard.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    user_id = request.session.get('pre_otp_user_id')
    if not user_id:
        messages.info(request, "Please enter your login credentials first.")
        return redirect('login')

    user = User.objects.filter(id=user_id).first()
    if not user:
        request.session.pop('pre_otp_user_id', None)
        return redirect('login')

    student = getattr(user, 'student', None)
    if not student:
        request.session.pop('pre_otp_user_id', None)
        return redirect('login')

    masked_email = mask_email(user.email)
    errors = []

    if request.method == 'POST':
        attempts = request.session.get('otp_attempts', 0)
        if attempts >= 5:
            # Invalidate any unused OTP
            StudentOTP.objects.filter(student=student, is_used=False).update(is_used=True)
            errors.append("Too many failed attempts. Please request a new verification code.")
            return render(request, 'verify_otp.html', {
                'masked_email': masked_email,
                'errors': errors,
                'too_many_attempts': True
            })

        submitted_otp = request.POST.get('otp', '').strip()

        if not submitted_otp:
            errors.append("Please enter the 6-digit verification code.")
        elif len(submitted_otp) != 6 or not submitted_otp.isdigit():
            errors.append("Verification code must be exactly 6 digits.")
        else:
            # Query latest active unused OTP for this student
            otp_record = StudentOTP.objects.filter(
                student=student,
                is_used=False
            ).order_by('-created_at').first()

            if not otp_record:
                errors.append("No active verification code found. Please request a new one.")
            elif otp_record.is_expired:
                errors.append("Verification code has expired. Please request a new code.")
            elif otp_record.otp != submitted_otp:
                request.session['otp_attempts'] = attempts + 1
                errors.append("Incorrect verification code. Please try again.")
            else:
                # Valid OTP! Mark as used atomically
                with transaction.atomic():
                    otp_record.is_used = True
                    otp_record.save(update_fields=['is_used'])

                # Clear session pre-login keys
                request.session.pop('pre_otp_user_id', None)
                request.session.pop('otp_attempts', None)
                request.session.pop('otp_resend_count', None)
                request.session.pop('otp_last_sent', None)

                # Complete student login!
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('dashboard')

    # Print current active OTP to the terminal whenever verification page is opened/refreshed
    active_otp = StudentOTP.objects.filter(
        student=student,
        is_used=False
    ).order_by('-created_at').first()
    if active_otp and not active_otp.is_expired:
        print("\n" + "=" * 55, flush=True)
        print(f"🔑 [CURRENT ACTIVE OTP] For: {user.username}", flush=True)
        print(f"👉 YOUR OTP CODE: >>> {active_otp.otp} <<<", flush=True)
        print("=" * 55 + "\n", flush=True)

    # Calculate remaining cooldown seconds from last OTP send timestamp
    cooldown_seconds = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)
    last_sent = request.session.get('otp_last_sent', 0)
    now_ts = timezone.now().timestamp()
    if last_sent:
        elapsed = now_ts - float(last_sent)
        remaining_cooldown = max(0, int(cooldown_seconds - elapsed))
    else:
        remaining_cooldown = 0

    return render(request, 'verify_otp.html', {
        'masked_email': masked_email,
        'errors': errors,
        'otp_expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 5),
        'cooldown_seconds': cooldown_seconds,
        'remaining_cooldown': remaining_cooldown,
    })


def resend_otp_view(request):
    """
    Generates and sends a new OTP for the pending student session, with rate limiting.
    """
    if request.method != 'POST':
        return redirect('verify_otp')

    user_id = request.session.get('pre_otp_user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.filter(id=user_id).first()
    if not user:
        return redirect('login')

    student = getattr(user, 'student', None)
    if not student:
        return redirect('login')

    # Rate limiting: max resend attempts per pending verification session (max 5)
    resend_count = request.session.get('otp_resend_count', 0)
    if resend_count >= 5:
        # Invalidate active unused OTPs for security
        StudentOTP.objects.filter(student=student, is_used=False).update(is_used=True)
        messages.error(request, "Maximum resend attempts reached. Please return to login and start again.")
        return redirect('verify_otp')

    # Cooldown enforcement: 60-second cooldown between resends
    cooldown_seconds = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)
    last_sent = request.session.get('otp_last_sent')
    now_ts = timezone.now().timestamp()
    if last_sent and (now_ts - float(last_sent) < cooldown_seconds):
        wait_seconds = max(1, int(cooldown_seconds - (now_ts - float(last_sent))))
        messages.warning(request, f"Please wait {wait_seconds} seconds before requesting another code.")
        return redirect('verify_otp')

    success, err = send_student_otp(request, user, student)
    if success:
        request.session['otp_attempts'] = 0
        request.session['otp_resend_count'] = resend_count + 1
        request.session['otp_last_sent'] = timezone.now().timestamp()
        messages.success(request, "A fresh verification code has been sent to your email.")
    else:
        messages.error(request, err)

    return redirect('verify_otp')


def logout_view(request):
    # Clear any pending OTP session data on logout
    request.session.pop('pre_otp_user_id', None)
    request.session.pop('otp_attempts', None)
    request.session.pop('otp_resend_count', None)
    request.session.pop('otp_last_sent', None)
    logout(request)
    return redirect('login')

@student_required
def dashboard(request):
    student = getattr(request.user, 'student', None)
    current_view = request.GET.get('view', 'overview')
    search_query = request.GET.get('search', '').strip()
    page_number = request.GET.get('page', 1)
    
    # Calculate statistics
    completed_quizzes = student.report_cards.count() if student else 0
    avg_score = student.report_cards.aggregate(Avg('percentage'))['percentage__avg'] if student else None
    avg_score_formatted = f"{round(avg_score, 1)}%" if avg_score is not None else "0%"
    
    # Retrieve available quizzes (subjects) with question counts
    base_subjects = Subject.objects.filter(questions__isnull=False).distinct().order_by('name')
    total_subjects_count = base_subjects.count()

    filtered_subjects = base_subjects
    if search_query:
        filtered_subjects = filtered_subjects.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        ).distinct()

    all_available_subjects = []
    for s in filtered_subjects:
        total_q = s.questions.count()
        all_available_subjects.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'total_questions': total_q
        })
        
    # Paginate with 6 subjects per page
    paginator = Paginator(all_available_subjects, 6)
    try:
        available_subjects = paginator.get_page(page_number)
    except Exception:
        available_subjects = paginator.get_page(1)

    # Get recent progress / report cards for this student
    recent_progress = []
    if student:
        recent_progress = student.report_cards.all().order_by('-created_at')
        
    context = {
        'student': student,
        'user': request.user,
        'completed_quizzes': completed_quizzes,
        'avg_score': avg_score_formatted,
        'subjects_count': total_subjects_count,
        'available_subjects': available_subjects,
        'search_query': search_query,
        'recent_progress': recent_progress,
        'current_view': current_view,
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
                    
                    req_msg = "Profile update request submitted to Admin! Your profile will be updated once approved by the administrator."
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
        answer_records = []
        
        for idx, q in enumerate(questions, start=1):
            ans_key = f"question_{q.id}"
            student_answer = request.POST.get(ans_key, '').strip()
            is_attempted = bool(student_answer)
            is_correct = False
            student_ans_text = ""
            correct_ans_letter = ""
            correct_ans_text = ""
            
            if q.question_type == 'mcq':
                correct_ans_letter = (q.correct_option or 'A').strip().upper()
                opt_map = {
                    'A': q.option_a or '',
                    'B': q.option_b or '',
                    'C': q.option_c or '',
                    'D': q.option_d or '',
                }
                correct_ans_text = opt_map.get(correct_ans_letter, '')
                
                if is_attempted:
                    attempted_count += 1
                    student_ans_letter = student_answer.strip().upper()
                    student_ans_text = opt_map.get(student_ans_letter, student_answer)
                    if student_ans_letter == correct_ans_letter:
                        is_correct = True
                        correct_count += 1
            else:
                # Q&A: text question
                correct_ans_letter = ""
                correct_ans_text = (q.option_a or '').strip()
                if is_attempted:
                    attempted_count += 1
                    student_ans_text = student_answer
                    if student_answer.lower() == correct_ans_text.lower():
                        is_correct = True
                        correct_count += 1
            
            answer_records.append(ReportCardAnswer(
                question=q,
                question_text=q.question_text,
                question_type=q.question_type,
                option_a=q.option_a or '',
                option_b=q.option_b or '',
                option_c=q.option_c or '',
                option_d=q.option_d or '',
                student_answer=student_answer,
                student_answer_text=student_ans_text,
                correct_answer=correct_ans_letter if q.question_type == 'mcq' else correct_ans_text,
                correct_answer_text=correct_ans_text,
                is_correct=is_correct,
                is_attempted=is_attempted,
                order=idx,
            ))
                    
        total_questions = questions.count()
        wrong_answers = attempted_count - correct_count
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
            
        with transaction.atomic():
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
            
            for ans in answer_records:
                ans.report_card = report_card
            ReportCardAnswer.objects.bulk_create(answer_records)
        
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
    report_card = get_object_or_404(
        ReportCard.objects.prefetch_related('answers'),
        id=pk,
        student=student
    )
    return render(request, 'report_card.html', {
        'student': student,
        'report_card': report_card,
    })
