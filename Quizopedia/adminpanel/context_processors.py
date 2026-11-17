from user.models import ProfileUpdateRequest, Subject, Contact

def pending_approvals_count(request):
    data = {
        'pending_approvals_count': 0,
        'sidebar_mcq_count': 0,
        'sidebar_qna_count': 0,
        'new_contacts_count': 0,
        'student_mcq_count': 0,
        'student_qna_count': 0,
        'student_total_quizzes_count': 0,
    }
    if request.user.is_authenticated:
        mcq_count = Subject.objects.filter(questions__question_type='mcq').distinct().count()
        qna_count = Subject.objects.filter(questions__question_type='qna').distinct().count()
        total_count = Subject.objects.filter(questions__isnull=False).distinct().count()
        data['student_mcq_count'] = mcq_count
        data['student_qna_count'] = qna_count
        data['student_total_quizzes_count'] = total_count
        data['sidebar_mcq_count'] = mcq_count
        data['sidebar_qna_count'] = qna_count

        if request.user.is_staff or request.user.is_superuser:
            data['pending_approvals_count'] = ProfileUpdateRequest.objects.filter(status='pending').count()
            data['new_contacts_count'] = Contact.objects.filter(status='new').count()
    return data
