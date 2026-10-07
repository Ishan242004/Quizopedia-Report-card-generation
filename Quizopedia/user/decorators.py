from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps

def student_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        if not hasattr(request.user, 'student'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
