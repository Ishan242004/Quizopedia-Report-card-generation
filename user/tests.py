from django.test import TestCase
from django.urls import reverse
from .models import Student

class RegistrationFlowTests(TestCase):
    def test_register_get_request(self):
        """GET request to registration page should render the register template."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_validation_errors(self):
        """Invalid registration data should keep user on registration page and display errors."""
        # 1. Password mismatch
        response = self.client.post(reverse('register'), {
            'username': 'john_doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'differentpassword',
            'terms': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Passwords do not match.')
        # Confirm student was not saved
        self.assertEqual(Student.objects.count(), 0)

        # 2. Too short username
        response = self.client.post(reverse('register'), {
            'username': 'jo',
            'email': 'john@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username must be at least 3 characters.')
        self.assertEqual(Student.objects.count(), 0)

        # 3. Missing terms agreement
        response = self.client.post(reverse('register'), {
            'username': 'john_doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You must agree to the Terms &amp; Conditions.')
        self.assertEqual(Student.objects.count(), 0)

    def test_register_duplicate_username_and_email(self):
        """Duplicate username or email should return validation errors."""
        from django.contrib.auth.models import User
        # Create an existing student
        user = User.objects.create_user(
            username='existing_user',
            email='existing@example.com',
            password='password123'
        )
        Student.objects.create(
            user=user,
            phone='1234567890'
        )

        # Duplicate username
        response = self.client.post(reverse('register'), {
            'username': 'existing_user',
            'email': 'new@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already exists.')

        # Duplicate email
        response = self.client.post(reverse('register'), {
            'username': 'new_user',
            'email': 'existing@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email already exists.')

    def test_register_success(self):
        """Valid registration data should save Student, stay on registration page, and display student info."""
        response = self.client.post(reverse('register'), {
            'username': 'john_doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': 'on'
        })
        # Stays on the same page, status 200
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Registration Successful!')
        self.assertContains(response, 'john_doe')
        self.assertContains(response, 'john@example.com')
        self.assertContains(response, '1234567890')
        
        # Check database entry
        self.assertEqual(Student.objects.count(), 1)
        student = Student.objects.get(user__username='john_doe')
        self.assertEqual(student.email, 'john@example.com')
        self.assertEqual(student.phone, '1234567890')
        from django.contrib.auth.hashers import check_password
        self.assertTrue(check_password('password123', student.user.password))

    def test_student_registered_in_admin(self):
        """Verify that Student model is registered in django admin."""
        from django.contrib import admin
        self.assertIn(Student, admin.site._registry)

class IntegrationFlowTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        # Create student user and profile
        self.student_user = User.objects.create_user(username='student_test', email='student@example.com', password='password123')
        self.student = Student.objects.create(user=self.student_user, phone='1234567890')
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(username='admin_test', email='admin@example.com', password='password123')

    def test_student_login_redirection(self):
        # Post login as student
        response = self.client.post(reverse('login'), {
            'username': 'student_test',
            'password': 'password123'
        })
        # Should redirect to student dashboard
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_login_by_email_redirection(self):
        # Post login as student using email
        response = self.client.post(reverse('login'), {
            'username': 'student@example.com',
            'password': 'password123'
        })
        # Should redirect to student dashboard
        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_login_redirection(self):
        # Post login as admin
        response = self.client.post(reverse('login'), {
            'username': 'admin_test',
            'password': 'password123'
        })
        # Should redirect to admin dashboard
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_student_cannot_access_admin_dashboard(self):
        # Login as student
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_cannot_access_student_dashboard(self):
        # Login as admin
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('dashboard'))
        # Should redirect to admin dashboard
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_logout(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
