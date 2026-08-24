# Quizopedia - Report Card Generation (Core Setup)

This project implements a streamlined student and admin authentication and management system using Django, styled with custom Glassmorphism/ambient-blob aesthetics using Tailwind CSS and Lucide icons.

---

## Core Features (Tasks 1-6)

1. **Django Project Initialization**: Fully configured project settings including database, static, and media directories.
2. **Admin & Student Profiles**:
   - `Student` model (extending Django's built-in `User` with custom `phone` field).
   - `Admin` model (extending Django's built-in `User` with custom `phone` field).
3. **Django Admin Registrations**: Both models are registered and fully managed under the default Django Admin panel (`/admin/`).
4. **Secure Case-Insensitive Authentication**:
   - Login page (`/login/`) supports secure authentication using password and either the registered **email address** or **username** (both looked up case-insensitively).
   - Registration page (`/register/`) for students with real-time validation and success state displays.
   - Logout redirection.
5. **Role-Based Redirection & Dashboards**:
   - **Student Dashboard** (`/dashboard/`): Displays the logged-in student's profile information (Username, Email, Phone).
   - **Admin Dashboard** (`/admin-dashboard/`): Displays summary statistics (Total Students count) and acts as the entry point for student account management.
   - **Student Accounts Manager** (`/admin-dashboard/students/`): Allows administrators to view, add, edit, and delete student accounts directly.

---

## Technical Layout

- **Settings**: [Quizopedia/settings.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/Quizopedia/settings.py)
- **URLs**:
  - Global: [Quizopedia/urls.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/Quizopedia/urls.py)
  - Student: [user/urls.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/urls.py)
  - Admin: [adminpanel/urls.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/adminpanel/urls.py)
- **Models**:
  - Student: `Student` in [user/models.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/models.py)
  - Admin: `Admin` in [adminpanel/models.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/adminpanel/models.py)
- **Decorators**: [user/decorators.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/decorators.py) (includes `@student_required` and `@admin_required`)
- **Unit Tests**: [user/tests.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/tests.py)

---

## Running the Application

### 1. Activate Environment & Run Dev Server
In your PowerShell terminal:
```powershell
# Navigate to environment
cd myenv
.\Scripts\activate

# Navigate to project and run development server
cd Quizopedia
python manage.py runserver
```

### 2. Run Test Suite
To execute the unit tests verifying authentication, validations, and role-based redirection:
```powershell
python manage.py test
```
