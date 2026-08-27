from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from user.models import Student, ProfileUpdateRequest, Subject, Question, ReportCard
from user.decorators import admin_required
from .forms import QuestionForm, QuestionEditForm
import re

@admin_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    subject_count = Subject.objects.filter(questions__isnull=False).distinct().count()
    report_card_count = ReportCard.objects.count()
    
    # Total questions = total Question rows in DB (each row is one question)
    question_count = Question.objects.count()
    
    context = {
        'total_students': total_students,
        'question_count': question_count,
        'subject_count': subject_count,
        'report_card_count': report_card_count,
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
                user.first_name = req.name
                user.email = req.email
                user.save()
                
                student = req.student
                student.phone = req.phone
                student.save()
                
                req.status = 'approved'
                req.save()
                success_msg = f"Profile update request for '{user.username}' has been approved."
                
        elif action == 'reject':
            req.status = 'rejected'
            req.save()
            success_msg = f"Profile update request for '{req.student.user.username}' has been rejected."
            
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
    # Group questions by subject — show each subject as a card
    subjects = Subject.objects.filter(questions__isnull=False).distinct().order_by('name')
    subject_data = []
    for subject in subjects:
        qs = subject.questions.all()
        subject_data.append({
            'subject': subject,
            'count': qs.count(),
        })
    return render(request, 'adminpanel/question_list.html', {
        'subject_data': subject_data
    })


@admin_required
def subject_questions(request, pk):
    subject = get_object_or_404(Subject, id=pk)
    questions = subject.questions.all().order_by('id')
    return render(request, 'adminpanel/subject_questions.html', {
        'subject': subject,
        'questions': questions,
    })


def parse_mcq_text(text):
    blocks = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]
    parsed_questions = []

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        question_text = ""
        option_a = ""
        option_b = ""
        option_c = ""
        option_d = ""
        correct_option = "A"
        
        opt_a_re = re.compile(r'^[aA][).:\s]\s*(.*)$')
        opt_b_re = re.compile(r'^[bB][).:\s]\s*(.*)$')
        opt_c_re = re.compile(r'^[cC][).:\s]\s*(.*)$')
        opt_d_re = re.compile(r'^[dD][).:\s]\s*(.*)$')
        
        correct_ans_re = re.compile(r'^(?:correct\s+)?answer\s*:\s*([a-dA-D])(?:\s*|[).:].*)$', re.IGNORECASE)
        correct_ans_full_re = re.compile(r'^(?:correct\s+)?answer\s*:\s*([a-dA-D])\s*[).:\s]\s*(.*)$', re.IGNORECASE)
        # New: plain text answer format — "Correct Answer: Object Oriented Programming"
        correct_ans_text_re = re.compile(r'^(?:correct\s+)?answer\s*:\s*(.+)$', re.IGNORECASE)
        
        question_lines = []
        plain_answer = None   # For simple Q&A format (no A/B/C/D)
        
        for line in lines:
            ma = opt_a_re.match(line)
            mb = opt_b_re.match(line)
            mc = opt_c_re.match(line)
            md = opt_d_re.match(line)
            
            if ma:
                val = ma.group(1)
                if '*' in val:
                    correct_option = "A"
                    val = val.replace('*', '')
                option_a = val.strip()
            elif mb:
                val = mb.group(1)
                if '*' in val:
                    correct_option = "B"
                    val = val.replace('*', '')
                option_b = val.strip()
            elif mc:
                val = mc.group(1)
                if '*' in val:
                    correct_option = "C"
                    val = val.replace('*', '')
                option_c = val.strip()
            elif md:
                val = md.group(1)
                if '*' in val:
                    correct_option = "D"
                    val = val.replace('*', '')
                option_d = val.strip()
            else:
                m_ans = correct_ans_re.match(line)
                m_ans_full = correct_ans_full_re.match(line)
                m_ans_text = correct_ans_text_re.match(line)
                if m_ans:
                    correct_option = m_ans.group(1).upper()
                elif m_ans_full:
                    correct_option = m_ans_full.group(1).upper()
                elif line.lower().startswith('correct answer'):
                    # Check if it's a letter-based answer
                    found_letter = False
                    for letter in ['A', 'B', 'C', 'D']:
                        if f"{letter})" in line or f"{letter}." in line or f" {letter} " in line or line.rstrip().endswith(letter):
                            correct_option = letter
                            found_letter = True
                            break
                    if not found_letter and m_ans_text:
                        # Plain text answer like "Correct Answer: Object Oriented Programming"
                        plain_answer = m_ans_text.group(1).strip()
                else:
                    question_lines.append(line)
                    
        question_raw = " ".join(question_lines).strip()
        question_clean = re.sub(r'^\d+[\s.)-]+\s*', '', question_raw)
        
        # --- MCQ format (has A/B options) ---
        if question_clean and option_a and option_b:
            parsed_questions.append({
                'question_text': question_clean,
                'option_a': option_a,
                'option_b': option_b,
                'option_c': option_c,
                'option_d': option_d,
                'correct_option': correct_option
            })
        # --- Simple Q&A format (no options, just Correct Answer: text) ---
        elif question_clean and plain_answer:
            parsed_questions.append({
                'question_text': question_clean,
                'option_a': plain_answer,
                'option_b': '',
                'option_c': '',
                'option_d': '',
                'correct_option': 'A'
            })
            
    return parsed_questions


@admin_required
def question_add(request):
    errors = []
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            subject_input = form.cleaned_data['subject'].strip()
            question_text = form.cleaned_data['question_text'].strip()
            
            # Resolve subject (ID or name)
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
                
            # Parse pasted MCQ text
            parsed_questions = parse_mcq_text(question_text)
            if not parsed_questions:
                errors.append("Could not parse any valid MCQ questions from the input. Please follow the format shown in placeholder.")
            else:
                for pq in parsed_questions:
                    Question.objects.create(
                        subject=subject,
                        question_text=pq['question_text'],
                        option_a=pq['option_a'],
                        option_b=pq['option_b'],
                        option_c=pq['option_c'],
                        option_d=pq['option_d'],
                        correct_option=pq['correct_option']
                    )
                if len(parsed_questions) == 1:
                    messages.success(request, "Question added successfully.")
                else:
                    messages.success(request, f"Successfully parsed and added {len(parsed_questions)} questions.")
                return redirect('question_list')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    errors.append(err)
    else:
        form = QuestionForm()
    return render(request, 'adminpanel/question_form.html', {
        'form': form,
        'title': 'Add Question',
        'submit_text': 'Save Question',
        'errors': errors
    })


@admin_required
def question_edit(request, pk):
    question = get_object_or_404(Question, id=pk)
    errors = []
    if request.method == 'POST':
        form = QuestionEditForm(request.POST, instance=question)
        if form.is_valid():
            subject_input = form.cleaned_data['subject'].strip()
            
            # Resolve subject (ID or name)
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
                
            question = form.save(commit=False)
            question.subject = subject
            question.save()
            
            messages.success(request, "Question updated successfully.")
            return redirect('question_detail', pk=question.id)
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    errors.append(err)
    else:
        form = QuestionEditForm(instance=question, initial={
            'subject': question.subject.name
        })
    return render(request, 'adminpanel/question_form.html', {
        'form': form,
        'title': 'Edit Question',
        'submit_text': 'Save Question',
        'errors': errors
    })


@admin_required
def question_delete(request, pk):
    if request.method == 'POST':
        question = get_object_or_404(Question, id=pk)
        question.delete()
        messages.success(request, "Question deleted successfully.")
    return redirect('question_list')


@admin_required
def question_detail(request, pk):
    question = get_object_or_404(Question, id=pk)
    return render(request, 'adminpanel/question_detail.html', {
        'question': question
    })


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





