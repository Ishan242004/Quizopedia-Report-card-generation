from user.models import ProfileUpdateRequest

def pending_approvals_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        count = ProfileUpdateRequest.objects.filter(status='pending').count()
        return {'pending_approvals_count': count}
    return {'pending_approvals_count': 0}
