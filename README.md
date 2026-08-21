# Quizopedia - Student Registration Flow

This project implements a streamlined student registration system using Django, styled with custom Glassmorphism/ambient-blob aesthetics using Tailwind CSS and Lucide icons.

## Registration Process

The registration flow operates as follows:

1. **Accessing the Registration Page**: 
   - Open the `/register/` URL in the browser.

2. **Form Submission & Validations**:
   - Students register directly on the `/register/` page.
   - The system performs real-time client-side checks and backend server-side validations:
     - **Terms Agreement**: The student must agree to the Terms & Conditions.
     - **Username**: Must be at least 3 characters.
     - **Passwords**: Must match and satisfy basic strength requirements.
     - **Unique Constraints**: Automatically checks if the Username or Email is already registered in the database.

3. **Success State (Inline Display)**:
   - Upon successful registration, the student remains on the same `/register/` page.
   - The registration form is replaced with a **Success View** displaying the newly registered student's information:
     - **Username**
     - **Email Address**
     - **Phone Number**
   - A button is provided to **Register Another Student** if needed.
   - No separate `login.html` or login redirection is used, keeping the registration completely self-contained.

4. **Django Admin panel**:
   - The student data is stored using the `Student` model (`user/models.py`).
   - Registered student data is immediately available in the Django Admin interface.
   - The admin interface is routed to `/admin1/` (instead of the default `/admin/`).
   - The student entries can be managed under the **Students** section inside `/admin1/`.

---

## Technical Layout

- **URLs**: [Quizopedia/urls.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/Quizopedia/urls.py) and [user/urls.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/urls.py)
- **Model**: `Student` in [user/models.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/models.py)
- **View Logic**: [user/views.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/views.py)
- **Template**: [register.html](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/templates/register.html)
- **Admin Setup**: [user/admin.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/admin.py)
- **Unit Tests**: [user/tests.py](file:///c:/Users/Dell/Desktop/python%20task/Quizopedia%20card%20generation/myenv/Quizopedia/user/tests.py)

---

## Running the Application

### 1. Activate Environment & Run Dev Server
In your PowerShell terminal:
```powershell
# Navigate to environment
cd myenv
Scripts\activate

# Navigate to project and run development server
cd Quizopedia
python manage.py runserver
```

### 2. Run Test Suite
To execute unit tests verifying both the validation errors and successful registrations:
```powershell
python manage.py test
```
