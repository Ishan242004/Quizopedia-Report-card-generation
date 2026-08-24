from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from user.models import Student, Quiz, Question, StudentAttempt, ReportCard
from user.decorators import admin_required

@admin_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_quizzes = Quiz.objects.count()
    total_questions = Question.objects.count()
    total_attempts = StudentAttempt.objects.count()
    total_report_cards = ReportCard.objects.count()
    
    recent_attempts = StudentAttempt.objects.all().order_by('-completed_at')[:5]
    recent_report_cards = ReportCard.objects.all().order_by('-generated_at')[:5]
    
    context = {
        'total_students': total_students,
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'total_report_cards': total_report_cards,
        'recent_attempts': recent_attempts,
        'recent_report_cards': recent_report_cards,
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
def quiz_list(request):
    errors = []
    success_msg = None
    
    if request.method == 'POST':
        # Add Quiz
        if 'add_quiz' in request.POST:
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            total_marks = request.POST.get('total_marks', '100')
            
            if not title or not total_marks:
                errors.append("Title and total marks are required.")
            else:
                Quiz.objects.create(title=title, description=description, total_marks=int(total_marks))
                success_msg = f"Quiz '{title}' created successfully."
                
        # Edit Quiz
        elif 'edit_quiz' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            quiz = get_object_or_404(Quiz, id=quiz_id)
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            total_marks = request.POST.get('total_marks', '100')
            
            if not title or not total_marks:
                errors.append("Title and total marks are required.")
            else:
                quiz.title = title
                quiz.description = description
                quiz.total_marks = int(total_marks)
                quiz.save()
                success_msg = f"Quiz '{title}' updated successfully."
                
        # Delete Quiz
        elif 'delete_quiz' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            quiz = get_object_or_404(Quiz, id=quiz_id)
            title = quiz.title
            quiz.delete()
            success_msg = f"Quiz '{title}' deleted successfully."
            
    quizzes = Quiz.objects.all().order_by('id')
    return render(request, 'adminpanel/quizzes.html', {
        'quizzes': quizzes,
        'errors': errors,
        'success': success_msg
    })

@admin_required
def question_list(request):
    errors = []
    success_msg = None
    
    if request.method == 'POST':
        # Add Question
        if 'add_question' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            text = request.POST.get('text', '').strip()
            option_a = request.POST.get('option_a', '').strip()
            option_b = request.POST.get('option_b', '').strip()
            option_c = request.POST.get('option_c', '').strip()
            option_d = request.POST.get('option_d', '').strip()
            correct_option = request.POST.get('correct_option', '').strip()
            marks = request.POST.get('marks', '10')
            
            if not quiz_id or not text or not option_a or not option_b or not option_c or not option_d or not correct_option:
                errors.append("All fields are required.")
            else:
                quiz = get_object_or_404(Quiz, id=quiz_id)
                Question.objects.create(
                    quiz=quiz,
                    text=text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=correct_option,
                    marks=int(marks)
                )
                success_msg = "Question created successfully."
                
        # Edit Question
        elif 'edit_question' in request.POST:
            question_id = request.POST.get('question_id')
            question = get_object_or_404(Question, id=question_id)
            quiz_id = request.POST.get('quiz_id')
            text = request.POST.get('text', '').strip()
            option_a = request.POST.get('option_a', '').strip()
            option_b = request.POST.get('option_b', '').strip()
            option_c = request.POST.get('option_c', '').strip()
            option_d = request.POST.get('option_d', '').strip()
            correct_option = request.POST.get('correct_option', '').strip()
            marks = request.POST.get('marks', '10')
            
            if not quiz_id or not text or not option_a or not option_b or not option_c or not option_d or not correct_option:
                errors.append("All fields are required.")
            else:
                quiz = get_object_or_404(Quiz, id=quiz_id)
                question.quiz = quiz
                question.text = text
                question.option_a = option_a
                question.option_b = option_b
                question.option_c = option_c
                question.option_d = option_d
                question.correct_option = correct_option
                question.marks = int(marks)
                question.save()
                success_msg = "Question updated successfully."
                
        # Delete Question
        elif 'delete_question' in request.POST:
            question_id = request.POST.get('question_id')
            question = get_object_or_404(Question, id=question_id)
            question.delete()
            success_msg = "Question deleted successfully."
            
    questions = Question.objects.all().order_by('quiz__title', 'id')
    quizzes = Quiz.objects.all()
    return render(request, 'adminpanel/questions.html', {
        'questions': questions,
        'quizzes': quizzes,
        'errors': errors,
        'success': success_msg
    })

@admin_required
def attempt_list(request):
    errors = []
    success_msg = None
    
    if request.method == 'POST':
        # Delete Attempt
        if 'delete_attempt' in request.POST:
            attempt_id = request.POST.get('attempt_id')
            attempt = get_object_or_404(StudentAttempt, id=attempt_id)
            attempt.delete()
            success_msg = "Attempt deleted successfully."
            
    attempts = StudentAttempt.objects.all().order_by('-completed_at')
    return render(request, 'adminpanel/attempts.html', {
        'attempts': attempts,
        'errors': errors,
        'success': success_msg
    })

@admin_required
def report_card_list(request):
    errors = []
    success_msg = None
    
    if request.method == 'POST':
        # Add Report Card
        if 'add_report_card' in request.POST:
            student_id = request.POST.get('student_id')
            attempt_id = request.POST.get('attempt_id')
            grade = request.POST.get('grade', '').strip()
            remarks = request.POST.get('remarks', '').strip()
            
            if not student_id or not grade:
                errors.append("Student and Grade are required.")
            else:
                student = get_object_or_404(Student, id=student_id)
                attempt = get_object_or_404(StudentAttempt, id=attempt_id) if attempt_id else None
                # Check uniqueness of attempt link if specified
                if attempt and ReportCard.objects.filter(attempt=attempt).exists():
                    errors.append("This quiz attempt already has an associated report card.")
                else:
                    ReportCard.objects.create(
                        student=student,
                        attempt=attempt,
                        grade=grade,
                        remarks=remarks
                    )
                    success_msg = f"Report card created for student '{student.user.username}'."
                    
        # Edit Report Card
        elif 'edit_report_card' in request.POST:
            report_card_id = request.POST.get('report_card_id')
            report_card = get_object_or_404(ReportCard, id=report_card_id)
            grade = request.POST.get('grade', '').strip()
            remarks = request.POST.get('remarks', '').strip()
            
            if not grade:
                errors.append("Grade is required.")
            else:
                report_card.grade = grade
                report_card.remarks = remarks
                report_card.save()
                success_msg = f"Report card for '{report_card.student.user.username}' updated successfully."
                
        # Delete Report Card
        elif 'delete_report_card' in request.POST:
            report_card_id = request.POST.get('report_card_id')
            report_card = get_object_or_404(ReportCard, id=report_card_id)
            student_name = report_card.student.user.username
            report_card.delete()
            success_msg = f"Report card for '{student_name}' deleted successfully."
            
    report_cards = ReportCard.objects.all().order_by('-generated_at')
    students = Student.objects.all()
    attempts = StudentAttempt.objects.all().order_by('-completed_at')
    return render(request, 'adminpanel/report_cards.html', {
        'report_cards': report_cards,
        'students': students,
        'attempts': attempts,
        'errors': errors,
        'success': success_msg
    })
