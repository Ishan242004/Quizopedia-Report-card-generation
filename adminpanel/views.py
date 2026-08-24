from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from user.models import Student
from user.decorators import admin_required

@admin_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    
    context = {
        'total_students': total_students,
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


