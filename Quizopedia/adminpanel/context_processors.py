from user.models import ProfileUpdateRequest, Subject, Contact

def pending_approvals_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        count = ProfileUpdateRequest.objects.filter(status='pending').count()
        mcq_count = Subject.objects.filter(questions__question_type='mcq').distinct().count()
        qna_count = Subject.objects.filter(questions__question_type='qna').distinct().count()
        new_contacts = Contact.objects.filter(status='new').count()
        return {
            'pending_approvals_count': count,
            'sidebar_mcq_count': mcq_count,
            'sidebar_qna_count': qna_count,
            'new_contacts_count': new_contacts,
        }
    return {
        'pending_approvals_count': 0,
        'sidebar_mcq_count': 0,
        'sidebar_qna_count': 0,
        'new_contacts_count': 0,
    }
