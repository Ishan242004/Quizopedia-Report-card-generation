from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Student, ProfileUpdateRequest
from .decorators import student_required
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

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
    context = {
        'student': student,
        'user': request.user,
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


