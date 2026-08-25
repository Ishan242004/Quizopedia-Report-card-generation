from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Student
from .decorators import student_required

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
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not email or not phone:
            errors.append("Username, Email, and Phone are required.")
        else:
            # Unique checks
            if User.objects.exclude(id=request.user.id).filter(username__iexact=username).exists():
                errors.append("Username already exists.")
            elif User.objects.exclude(id=request.user.id).filter(email__iexact=email).exists():
                errors.append("Email already in use.")
            else:
                request.user.username = username
                request.user.email = email
                request.user.save()
                
                if student:
                    student.phone = phone
                    student.save()
                    
                if password:
                    request.user.set_password(password)
                    request.user.save()
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, request.user)
                    
                success_msg = "Profile updated successfully."
                
    return render(request, 'profile.html', {
        'student': student,
        'user': request.user,
        'errors': errors,
        'success': success_msg
    })


