from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from user.models import Student, ProfileUpdateRequest, Subject, Question, ReportCard
from user.decorators import admin_required
from .forms import (
    QuestionForm, QuestionEditForm,
    QnAAddForm, QnAEditForm,
    MCQBulkForm, MCQEditForm,
)
import re
import sys
from django.db.models import Q
from django.core.paginator import Paginator


def safe_print(text):
    """Safely print text to terminal, gracefully handling Windows cp1252 encoding limitations."""
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        try:
            encoding = getattr(sys.stdout, 'encoding', 'ascii') or 'ascii'
            safe_text = text.encode(encoding, errors='replace').decode(encoding)
            print(safe_text, flush=True)
        except Exception:
            print(text.encode('ascii', errors='replace').decode('ascii'), flush=True)


def send_profile_status_email(req, status, rejection_reason='', old_email=None):
    """
    Sends an email notification to the student regarding their profile update request
    (approved or rejected/cancelled), and prints the email clearly to the terminal console.
    """
    user = req.student.user
    student = req.student
    student_name = req.name or user.first_name or user.username

    if status == 'approved':
        subject = "Quizopedia - Profile Update Request Approved"
        recipients = [req.email]
        if old_email and old_email.lower() != req.email.lower():
            if old_email not in recipients:
                recipients.append(old_email)

        message = (
            f"Hello {student_name},\n\n"
            f"Great news! Your profile update request has been APPROVED by the administrator.\n\n"
            f"Updated Profile Details:\n"
            f"  * Full Name:     {req.name}\n"
            f"  * Email Address: {req.email}\n"
            f"  * Phone Number:  {req.phone}\n\n"
            f"These changes are now active on your Quizopedia account.\n\n"
            f"If you did not request this update, please contact the administrator immediately.\n\n"
            f"Best regards,\n"
            f"Quizopedia Learning Platform"
        )
    else:
        # Rejected / Cancelled
        subject = "Quizopedia - Profile Update Request Cancelled / Rejected"
        recipients = []
        if user.email:
            recipients.append(user.email)
        if req.email and req.email not in recipients:
            recipients.append(req.email)

        reason_text = rejection_reason.strip() if rejection_reason else "No specific reason provided by administrator."
        message = (
            f"Hello {student_name},\n\n"
            f"Your profile update request has been REVIEWED and CANCELLED / REJECTED by the administrator.\n\n"
            f"Requested Changes:\n"
            f"  * Requested Name:  {req.name}\n"
            f"  * Requested Email: {req.email}\n"
            f"  * Requested Phone: {req.phone}\n\n"
            f"Reason for Rejection:\n"
            f"  \"{reason_text}\"\n\n"
            f"Your existing profile details remain active and unchanged:\n"
            f"  * Current Name:  {user.first_name or user.username}\n"
            f"  * Current Email: {user.email}\n"
            f"  * Current Phone: {student.phone}\n\n"
            f"If you have questions or wish to submit new details, please log in to your Quizopedia profile.\n\n"
            f"Best regards,\n"
            f"Quizopedia Learning Platform"
        )

    # 1. Print formatted notification clearly to terminal console
    border = "=" * 65
    safe_print("\n" + border)
    if status == 'approved':
        safe_print("[EMAIL NOTIFICATION - PROFILE APPROVED]")
    else:
        safe_print("[EMAIL NOTIFICATION - PROFILE REJECTED / CANCELLED]")
    safe_print(f"Student:      {user.username} ({student_name})")
    safe_print(f"Recipient(s): {', '.join(recipients)}")
    safe_print(f"Subject:      {subject}")
    safe_print("-" * 65)
    for line in message.strip().splitlines():
        safe_print(line)
    safe_print(border + "\n")

    # 2. Send email via Django's mail backend (console backend or SMTP)
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@quizopedia.com')
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception as e:
        safe_print(f"[EMAIL DELIVERY NOTE]: {e}")


@admin_required
def admin_dashboard(request):
    errors = []
    success_msg = None

    # Handle quick approve / reject directly from dashboard if requested
    if request.method == 'POST' and 'action' in request.POST:
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        req = get_object_or_404(ProfileUpdateRequest, id=request_id)
        
        if action == 'approve':
            user = req.student.user
            if User.objects.exclude(id=user.id).filter(email__iexact=req.email).exists():
                errors.append(f"Cannot approve request. Email '{req.email}' is already in use by another user.")
            else:
                old_email = user.email
                user.first_name = req.name
                user.email = req.email
                user.save()
                
                student = req.student
                student.phone = req.phone
                student.save()
                
                req.status = 'approved'
                req.save()
                
                send_profile_status_email(req, status='approved', old_email=old_email)
                messages.success(request, f"Profile update request for '{user.username}' has been approved and applied! Notification email sent.")
                return redirect('admin_dashboard')
                
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            req.status = 'rejected'
            req.rejection_reason = rejection_reason or 'Rejected by administrator.'
            req.save()
            
            send_profile_status_email(req, status='rejected', rejection_reason=req.rejection_reason)
            messages.success(request, f"Profile update request for '{req.student.user.username}' has been rejected. Notification email sent.")
            return redirect('admin_dashboard')

    total_students = Student.objects.count()
    subject_count = Subject.objects.filter(questions__isnull=False).distinct().count()
    report_card_count = ReportCard.objects.count()
    question_count = Question.objects.count()
    
    pending_profile_requests = ProfileUpdateRequest.objects.filter(status='pending').order_by('-created_at')
    
    context = {
        'total_students': total_students,
        'question_count': question_count,
        'subject_count': subject_count,
        'report_card_count': report_card_count,
        'pending_profile_requests': pending_profile_requests,
        'errors': errors,
        'success': success_msg,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@admin_required
def student_list(request):
    errors = []
    success_msg = None
    
    if request.method == 'POST':
        # Add Student
        if 'add_student' in request.POST:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '')
            
            if not username or not email or not phone or not password:
                errors.append("All fields are required.")
            elif User.objects.filter(username=username).exists():
                errors.append("Username already exists.")
            elif User.objects.filter(email=email).exists():
                errors.append("Email already exists.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                Student.objects.create(user=user, phone=phone)
                success_msg = f"Student '{username}' created successfully."
                
        # Edit Student
        elif 'edit_student' in request.POST:
            student_id = request.POST.get('student_id')
            student = get_object_or_404(Student, id=student_id)
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            if not email or not phone:
                errors.append("Email and Phone are required.")
            elif User.objects.exclude(id=student.user.id).filter(email=email).exists():
                errors.append("Email already in use by another user.")
            else:
                student.phone = phone
                student.save()
                student.user.email = email
                student.user.save()
                success_msg = f"Student '{student.user.username}' updated successfully."
                
        # Delete Student
        elif 'delete_student' in request.POST:
            student_id = request.POST.get('student_id')
            student = get_object_or_404(Student, id=student_id)
            username = student.user.username
            student.delete()  # Cascade deletes student & associated User
            success_msg = f"Student '{username}' deleted successfully."
            
    students = Student.objects.all().order_by('id')
    return render(request, 'adminpanel/students.html', {
        'students': students,
        'errors': errors,
        'success': success_msg
    })

@admin_required
def admin_profile(request):
    errors = []
    success_msg = None
    user = request.user
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not email:
            errors.append("Username and Email are required.")
        else:
            if User.objects.exclude(id=user.id).filter(username__iexact=username).exists():
                errors.append("Username already exists.")
            elif User.objects.exclude(id=user.id).filter(email__iexact=email).exists():
                errors.append("Email already in use.")
            else:
                user.username = username
                user.email = email
                user.save()
                
                if password:
                    user.set_password(password)
                    user.save()
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, user)
                    
                success_msg = "Admin profile updated successfully."
                
    return render(request, 'adminpanel/profile.html', {
        'errors': errors,
        'success': success_msg
    })


@admin_required
def profile_approvals(request):
    errors = []
    success_msg = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        req = get_object_or_404(ProfileUpdateRequest, id=request_id)
        
        if action == 'approve':
            user = req.student.user
            # Ensure email uniqueness again at approval time
            if User.objects.exclude(id=user.id).filter(email__iexact=req.email).exists():
                errors.append(f"Cannot approve request. Email '{req.email}' is already in use by another user.")
            else:
                old_email = user.email
                user.first_name = req.name
                user.email = req.email
                user.save()
                
                student = req.student
                student.phone = req.phone
                student.save()
                
                req.status = 'approved'
                req.save()
                
                send_profile_status_email(req, status='approved', old_email=old_email)
                messages.success(request, f"Profile update request for '{user.username}' has been approved and applied! Notification email sent.")
                return redirect('admin_profile_approvals')
                
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            req.status = 'rejected'
            req.rejection_reason = rejection_reason or 'Rejected by administrator.'
            req.save()
            
            send_profile_status_email(req, status='rejected', rejection_reason=req.rejection_reason)
            messages.success(request, f"Profile update request for '{req.student.user.username}' has been rejected. Notification email sent.")
            return redirect('admin_profile_approvals')
            
    pending_requests = ProfileUpdateRequest.objects.filter(status='pending').order_by('-created_at')
    past_requests = ProfileUpdateRequest.objects.exclude(status='pending').order_by('-updated_at')[:15]
    
    return render(request, 'adminpanel/approvals.html', {
        'pending_requests': pending_requests,
        'past_requests': past_requests,
        'errors': errors,
        'success': success_msg
    })


@admin_required
def question_list(request):
    search_query = request.GET.get('search', '').strip()
    page_number = request.GET.get('page', 1)
    qtype = request.GET.get('type', '').strip().lower()

    # Precalculate quiz counts for both sections (for tab badges and counters)
    mcq_subjects_qs = Subject.objects.filter(questions__question_type='mcq').distinct()
    qna_subjects_qs = Subject.objects.filter(questions__question_type='qna').distinct()

    mcq_quizzes_count = mcq_subjects_qs.count()
    qna_quizzes_count = qna_subjects_qs.count()
    mcq_questions_count = Question.objects.filter(question_type='mcq').count()
    qna_questions_count = Question.objects.filter(question_type='qna').count()

    # If no type specified or invalid, choose sensible default:
    # If there are MCQ quizzes, default to 'mcq'
    # Otherwise if only QnA quizzes exist (e.g. test fixture), default to 'qna'
    # Otherwise default to 'mcq'
    if qtype not in ['mcq', 'qna']:
        if mcq_quizzes_count > 0:
            qtype = 'mcq'
        elif qna_quizzes_count > 0:
            qtype = 'qna'
        else:
            qtype = 'mcq'

    # Filter subjects specifically belonging to the active section
    subjects_qs = Subject.objects.filter(questions__question_type=qtype).distinct().order_by('name')
    total_subjects_count = subjects_qs.count()

    if search_query:
        subjects_qs = subjects_qs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(questions__question_text__icontains=search_query, questions__question_type=qtype)
        ).distinct()

    subject_data = []
    for subject in subjects_qs:
        count = subject.questions.filter(question_type=qtype).count()
        subject_data.append({
            'subject': subject,
            'count': count,
            'qtype': qtype,
        })

    paginator = Paginator(subject_data, 6)
    try:
        page_obj = paginator.get_page(page_number)
    except Exception:
        page_obj = paginator.get_page(1)

    return render(request, 'adminpanel/question_list.html', {
        'subject_data': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_subjects_count': total_subjects_count,
        'active_qtype': qtype,
        'mcq_quizzes_count': mcq_quizzes_count,
        'qna_quizzes_count': qna_quizzes_count,
        'mcq_questions_count': mcq_questions_count,
        'qna_questions_count': qna_questions_count,
    })


@admin_required
def subject_questions(request, pk):
    subject = get_object_or_404(Subject, id=pk)
    qtype = request.GET.get('type', '').strip().lower()

    if qtype in ['mcq', 'qna']:
        questions = subject.questions.filter(question_type=qtype).order_by('id')
    else:
        questions = subject.questions.all().order_by('id')
        if questions.filter(question_type='mcq').exists() and not questions.filter(question_type='qna').exists():
            qtype = 'mcq'
        elif questions.filter(question_type='qna').exists() and not questions.filter(question_type='mcq').exists():
            qtype = 'qna'
        else:
            qtype = 'mcq'

    return render(request, 'adminpanel/subject_questions.html', {
        'subject': subject,
        'questions': questions,
        'active_qtype': qtype,
    })


# =============================================================================
# HELPER: Resolve subject name/ID to Subject object
# =============================================================================

def _resolve_subject(subject_input):
    """Resolve a subject input (name or ID string) to a Subject object."""
    subject_input = subject_input.strip()
    if subject_input.isdigit():
        subject = Subject.objects.filter(id=int(subject_input)).first()
        if not subject:
            subject, created = Subject.objects.get_or_create(
                name__iexact=subject_input,
                defaults={'name': subject_input}
            )
    else:
        subject, created = Subject.objects.get_or_create(
            name__iexact=subject_input,
            defaults={'name': subject_input}
        )
    return subject


# =============================================================================
# QUESTION TYPE SELECTION
# =============================================================================

@admin_required
def question_type_select(request):
    """Show question type selection page: Q&A or MCQ."""
    subject = request.GET.get('subject', '').strip()
    return render(request, 'adminpanel/question_type_select.html', {'subject': subject})


# =============================================================================
# QUESTION & ANSWER — ADD (Bulk / Single with Preview & Validation)
# =============================================================================

def parse_qna_bulk(text):
    """
    Parse bulk Q&A text into a list of question dicts.
    Returns (parsed_questions, errors).
    
    Each parsed question is a dict with:
        question_text, answer
    """
    if not text or not text.strip():
        return [], ["Question text is required."]
    
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove format introductory lines (e.g. "Format 1 – Simple Q&A...") and convert "---" lines
    cleaned_lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if re.match(r'^Format\s*\d+\b', stripped, re.IGNORECASE):
            continue
        if re.match(r'^[-=_*]{3,}$', stripped):
            cleaned_lines.append('')
            continue
        cleaned_lines.append(line)
    
    normalized_text = '\n'.join(cleaned_lines)
    raw_blocks = re.split(r'\n\s*\n', normalized_text)
    
    blocks = []
    for raw_block in raw_blocks:
        raw_block = raw_block.strip()
        if not raw_block:
            continue
        # Split blocks that contain multiple question markers like "Q1.", "Q2.", "Question 1:", etc.
        parts = re.split(r'(?=^(?:Q\d+|Question\s*\d+|\d+\.)[.\s):])', raw_block, flags=re.MULTILINE)
        for part in parts:
            part = part.strip()
            if part:
                blocks.append(part)
    
    if not blocks:
        return [], ["Could not find any questions in the input. Please follow the format shown in the placeholder."]
    
    parsed_questions = []
    errors = []
    
    ans_pattern = re.compile(
        r'^(?:(?:Correct\s+)?Answer|Ans|Correct\s*Option)\s*[:\-]\s*(.+)$',
        re.IGNORECASE
    )
    
    for idx, block in enumerate(blocks):
        q_num = idx + 1
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
        
        q_lines = []
        answer = ""
        
        for line in lines:
            m_ans = ans_pattern.match(line)
            if m_ans:
                answer = m_ans.group(1).strip()
            else:
                q_lines.append(line)
        
        q_text_raw = " ".join(q_lines).strip()
        q_text = re.sub(r'^(?:Question\s*\d+|Q\d+|Q|\d+)[.\s):\-]+\s*', '', q_text_raw, flags=re.IGNORECASE).strip()
        
        if not q_text and not answer:
            continue
            
        q_errors = []
        if not q_text:
            q_errors.append(f"Question {q_num}: Question text is missing.")
        if not answer:
            q_errors.append(f"Question {q_num}: Correct Answer is missing. (Format: Correct Answer: your answer)")
            
        if q_errors:
            errors.extend(q_errors)
        else:
            parsed_questions.append({
                'question_text': q_text,
                'answer': answer,
            })
            
    return parsed_questions, errors


@admin_required
def question_add_qna(request):
    """Add Question & Answer (supports single or bulk format)."""
    errors = []
    
    # Check for pre-selected subject via GET parameter
    subject_param = (request.GET.get('subject') or request.GET.get('subject_id') or '').strip()
    initial_subject = ''
    selected_subject = None
    if subject_param:
        if subject_param.isdigit():
            selected_subject = Subject.objects.filter(id=int(subject_param)).first()
            initial_subject = selected_subject.name if selected_subject else subject_param
        else:
            initial_subject = subject_param
            selected_subject = Subject.objects.filter(name__iexact=subject_param).first()

    if request.method == 'POST':
        form = QnAAddForm(request.POST)
        if form.is_valid():
            subject = _resolve_subject(form.cleaned_data['subject'])
            q_text_input = form.cleaned_data['question_text'].strip()
            ans_input = form.cleaned_data.get('answer', '').strip() if form.cleaned_data.get('answer') else ''
            
            # Check if answer was provided in a separate field (backward compatibility for direct POST/tests)
            # and question_text doesn't contain answer keyword
            if ans_input and not re.search(r'(?:(?:Correct\s+)?Answer|Ans)\s*:', q_text_input, re.IGNORECASE):
                Question.objects.create(
                    subject=subject,
                    question_type='qna',
                    question_text=q_text_input,
                    option_a=ans_input,
                    option_b='',
                    option_c='',
                    option_d='',
                    correct_option='A',
                )
                messages.success(request, "Question added successfully.")
                return redirect('subject_questions', pk=subject.id)
            
            # Otherwise parse Q&A text (bulk or single format with Correct Answer:)
            parsed_questions, parse_errors = parse_qna_bulk(q_text_input)
            
            if parse_errors:
                errors = ["Could not import questions."] + parse_errors
            elif not parsed_questions:
                errors = ["Could not find any valid questions in the input. Please follow the format shown in the placeholder."]
            else:
                try:
                    with transaction.atomic():
                        for pq in parsed_questions:
                            Question.objects.create(
                                subject=subject,
                                question_type='qna',
                                question_text=pq['question_text'],
                                option_a=pq['answer'],
                                option_b='',
                                option_c='',
                                option_d='',
                                correct_option='A',
                            )
                    count = len(parsed_questions)
                    messages.success(request, f"{count} question{'s' if count > 1 else ''} added successfully.")
                    return redirect('subject_questions', pk=subject.id)
                except Exception as e:
                    errors.append(f"An error occurred while saving questions: {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    errors.append(err)
    else:
        form = QnAAddForm(initial={'subject': initial_subject} if initial_subject else None)
        
    return render(request, 'adminpanel/question_add_qna.html', {
        'form': form,
        'errors': errors,
        'selected_subject': selected_subject,
    })


# =============================================================================
# 4 OPTION MCQ — BULK ADD with validation & atomic save
# =============================================================================

def parse_mcq_bulk(text):
    """
    Parse bulk MCQ text into a list of question dicts.
    Returns (parsed_questions, errors).
    
    Each parsed question is a dict with:
        question_text, option_a, option_b, option_c, option_d, correct_option
    
    errors is a list of strings describing per-question validation failures.
    """
    # First normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove format introductory lines (e.g. "Format 2 – MCQ...") and convert "---" lines
    cleaned_lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if re.match(r'^Format\s*\d+\b', stripped, re.IGNORECASE):
            continue
        if re.match(r'^[-=_*]{3,}$', stripped):
            cleaned_lines.append('')
            continue
        cleaned_lines.append(line)
    
    normalized_text = '\n'.join(cleaned_lines)
    raw_blocks = re.split(r'\n\s*\n', normalized_text)
    
    # Further split blocks that contain multiple questions (Q1... Q2... in same block)
    blocks = []
    for raw_block in raw_blocks:
        raw_block = raw_block.strip()
        if not raw_block:
            continue
        # Check if block contains multiple question markers
        parts = re.split(r'(?=^(?:Q\d+|Question\s*\d+|\d+\.)[.\s):])', raw_block, flags=re.MULTILINE)
        for part in parts:
            part = part.strip()
            if part:
                blocks.append(part)
    
    if not blocks:
        return [], ["Could not find any questions in the input. Please follow the format shown in the placeholder."]
    
    parsed_questions = []
    errors = []
    
    for idx, block in enumerate(blocks):
        q_num = idx + 1
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
        
        question_text = ""
        option_a = ""
        option_b = ""
        option_c = ""
        option_d = ""
        correct_option = ""
        
        # Regex patterns for options
        opt_a_re = re.compile(r'^[Aa]\s*[).:\-]\s*(.+)$')
        opt_b_re = re.compile(r'^[Bb]\s*[).:\-]\s*(.+)$')
        opt_c_re = re.compile(r'^[Cc]\s*[).:\-]\s*(.+)$')
        opt_d_re = re.compile(r'^[Dd]\s*[).:\-]\s*(.+)$')
        correct_re = re.compile(r'^[Cc]orrect\s+[Aa]nswer\s*:\s*([A-Da-d])\s*$', re.IGNORECASE)
        
        question_lines = []
        
        for line in lines:
            ma = opt_a_re.match(line)
            mb = opt_b_re.match(line)
            mc = opt_c_re.match(line)
            md = opt_d_re.match(line)
            mcorr = correct_re.match(line)
            
            if mcorr:
                correct_option = mcorr.group(1).upper()
            elif ma:
                option_a = ma.group(1).strip()
            elif mb:
                option_b = mb.group(1).strip()
            elif mc:
                option_c = mc.group(1).strip()
            elif md:
                option_d = md.group(1).strip()
            else:
                question_lines.append(line)
        
        # Clean question text — remove leading Q number prefix
        question_raw = " ".join(question_lines).strip()
        question_text = re.sub(r'^(?:Question\s*\d+|Q\d+|Q|\d+)[.\s):\-]+\s*', '', question_raw, flags=re.IGNORECASE).strip()
        
        # --- Validation ---
        q_errors = []
        
        if not question_text:
            q_errors.append(f"Question {q_num}: Question text is missing.")
        if not option_a:
            q_errors.append(f"Question {q_num}: Option A is missing.")
        if not option_b:
            q_errors.append(f"Question {q_num}: Option B is missing.")
        if not option_c:
            q_errors.append(f"Question {q_num}: Option C is missing.")
        if not option_d:
            q_errors.append(f"Question {q_num}: Option D is missing.")
        if not correct_option:
            q_errors.append(f"Question {q_num}: Correct Answer is missing.")
        elif correct_option not in ('A', 'B', 'C', 'D'):
            q_errors.append(f"Question {q_num}: Correct Answer must be A, B, C or D.")
        
        if q_errors:
            errors.extend(q_errors)
        else:
            parsed_questions.append({
                'question_text': question_text,
                'option_a': option_a,
                'option_b': option_b,
                'option_c': option_c,
                'option_d': option_d,
                'correct_option': correct_option,
            })
    
    return parsed_questions, errors


@admin_required
def question_add_mcq(request):
    """Bulk add MCQ questions with validation and atomic save."""
    errors = []
    preview_questions = None
    
    # Check for pre-selected subject via GET parameter
    subject_param = (request.GET.get('subject') or request.GET.get('subject_id') or '').strip()
    initial_subject = ''
    selected_subject = None
    if subject_param:
        if subject_param.isdigit():
            selected_subject = Subject.objects.filter(id=int(subject_param)).first()
            initial_subject = selected_subject.name if selected_subject else subject_param
        else:
            initial_subject = subject_param
            selected_subject = Subject.objects.filter(name__iexact=subject_param).first()
    
    if request.method == 'POST':
        form = MCQBulkForm(request.POST)
        if form.is_valid():
            subject = _resolve_subject(form.cleaned_data['subject'])
            mcq_text = form.cleaned_data['mcq_text']
            
            parsed_questions, parse_errors = parse_mcq_bulk(mcq_text)
            
            if parse_errors:
                errors = ["Could not import questions."] + parse_errors
            elif not parsed_questions:
                errors = ["Could not find any valid MCQ questions in the input. Please follow the format shown in the placeholder."]
            else:
                # Atomic save — all or nothing
                try:
                    with transaction.atomic():
                        for pq in parsed_questions:
                            Question.objects.create(
                                subject=subject,
                                question_type='mcq',
                                question_text=pq['question_text'],
                                option_a=pq['option_a'],
                                option_b=pq['option_b'],
                                option_c=pq['option_c'],
                                option_d=pq['option_d'],
                                correct_option=pq['correct_option'],
                            )
                    count = len(parsed_questions)
                    messages.success(request, f"{count} question{'s' if count > 1 else ''} added successfully.")
                    return redirect('subject_questions', pk=subject.id)
                except Exception as e:
                    errors.append(f"An error occurred while saving questions: {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    errors.append(err)
    else:
        form = MCQBulkForm(initial={'subject': initial_subject} if initial_subject else None)
    
    return render(request, 'adminpanel/question_add_mcq.html', {
        'form': form,
        'errors': errors,
        'selected_subject': selected_subject,
    })


# =============================================================================
# QUESTION EDIT — Routes to Q&A or MCQ edit based on question_type
# =============================================================================

@admin_required
def question_edit(request, pk):
    question = get_object_or_404(Question, id=pk)
    errors = []
    
    if question.is_mcq:
        return _edit_mcq(request, question, errors)
    else:
        return _edit_qna(request, question, errors)


def _edit_qna(request, question, errors):
    """Edit a Q&A question."""
    if request.method == 'POST':
        form = QnAEditForm(request.POST)
        if form.is_valid():
            subject = _resolve_subject(form.cleaned_data['subject'])
            question.subject = subject
            question.question_text = form.cleaned_data['question_text'].strip()
            question.option_a = form.cleaned_data['answer'].strip()
            question.option_b = ''
            question.option_c = ''
            question.option_d = ''
            question.correct_option = 'A'
            question.question_type = 'qna'
            question.save()
            messages.success(request, "Question updated successfully.")
            return redirect('question_detail', pk=question.id)
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    errors.append(err)
    else:
        form = QnAEditForm(initial={
            'subject': question.subject.name,
            'question_text': question.question_text,
            'answer': question.option_a,
        })
    
    return render(request, 'adminpanel/question_edit_qna.html', {
        'form': form,
        'question': question,
        'errors': errors,
    })


def _edit_mcq(request, question, errors):
    """Edit an MCQ question."""
    if request.method == 'POST':
        form = MCQEditForm(request.POST, instance=question)
        subject_input = request.POST.get('subject', '').strip()
        if form.is_valid() and subject_input:
            subject = _resolve_subject(subject_input)
            question = form.save(commit=False)
            question.subject = subject
            question.question_type = 'mcq'
            question.save()
            messages.success(request, "Question updated successfully.")
            return redirect('question_detail', pk=question.id)
        else:
            if not subject_input:
                errors.append("Subject is required.")
            for field, errs in form.errors.items():
                for err in errs:
                    errors.append(err)
    else:
        form = MCQEditForm(instance=question, initial={
            'subject': question.subject.name,
        })
    
    return render(request, 'adminpanel/question_edit_mcq.html', {
        'form': form,
        'question': question,
        'errors': errors,
    })


# =============================================================================
# QUESTION DELETE (unchanged)
# =============================================================================

@admin_required
def question_delete(request, pk):
    if request.method == 'POST':
        question = get_object_or_404(Question, id=pk)
        subject_id = question.subject.id
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect('subject_questions', pk=subject_id)
    return redirect('question_list')


# =============================================================================
# QUIZ / SUBJECT DELETE — Delete entire quiz and all its questions
# =============================================================================

@admin_required
def subject_delete(request, pk):
    """Delete an entire quiz/subject and all its associated questions."""
    qtype = request.GET.get('type') or request.POST.get('type') or ''
    if request.method == 'POST':
        subject = get_object_or_404(Subject, id=pk)
        subject_name = subject.name
        with transaction.atomic():
            subject.delete()
        messages.success(request, f"Quiz '{subject_name}' and all its questions deleted successfully.")
    if qtype in ['mcq', 'qna']:
        return redirect(f"{reverse('question_list')}?type={qtype}")
    return redirect('question_list')


# =============================================================================
# QUESTION DETAIL (unchanged)
# =============================================================================

@admin_required
def question_detail(request, pk):
    question = get_object_or_404(Question, id=pk)
    return render(request, 'adminpanel/question_detail.html', {
        'question': question
    })


# =============================================================================
# LEGACY: Original question_add (kept as fallback, now redirects to type select)
# =============================================================================

@admin_required
def question_add(request):
    """Legacy add — now redirects to type selection."""
    return redirect('question_type_select')


# =============================================================================
# REPORT CARDS (unchanged)
# =============================================================================

@admin_required
def admin_report_cards(request):
    report_cards = ReportCard.objects.select_related('student__user', 'subject').all().order_by('-created_at')
    return render(request, 'adminpanel/report_cards.html', {
        'report_cards': report_cards
    })


@admin_required
def admin_report_card_detail(request, pk):
    report_card = get_object_or_404(ReportCard, id=pk)
    return render(request, 'adminpanel/report_card_detail.html', {
        'report_card': report_card
    })


@admin_required
def admin_report_card_delete(request, pk):
    if request.method == 'POST':
        report_card = get_object_or_404(ReportCard, id=pk)
        report_card.delete()
        messages.success(request, "Report card deleted successfully.")
    return redirect('admin_report_cards')
