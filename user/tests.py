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

    def test_student_profile_get_unauthenticated(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('profile'))

    def test_student_profile_get_authenticated(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertContains(response, 'student_test')
        self.assertContains(response, 'student@example.com')

    def test_student_profile_post_update(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.post(reverse('profile'), {
            'name': 'John Doe',
            'email': 'updated@example.com',
            'phone': '0987654321',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile update submitted successfully. Pending Admin Approval.')
        
        # Verify db updates: password updated immediately, but name, email, phone not updated in User/Student
        self.student_user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.student_user.first_name, '')
        self.assertEqual(self.student_user.email, 'student@example.com')
        self.assertEqual(self.student.phone, '1234567890')
        from django.contrib.auth.hashers import check_password
        self.assertTrue(check_password('newpassword123', self.student_user.password))
        
        # Verify ProfileUpdateRequest created
        from .models import ProfileUpdateRequest
        self.assertEqual(ProfileUpdateRequest.objects.count(), 1)
        req = ProfileUpdateRequest.objects.first()
        self.assertEqual(req.name, 'John Doe')
        self.assertEqual(req.email, 'updated@example.com')
        self.assertEqual(req.phone, '0987654321')
        self.assertEqual(req.status, 'pending')

    def test_admin_approves_profile_update(self):
        from .models import ProfileUpdateRequest
        req = ProfileUpdateRequest.objects.create(
            student=self.student,
            name='Approved Name',
            email='approved@example.com',
            phone='0987654321',
            status='pending'
        )
        # Login as admin
        self.client.login(username='admin_test', password='password123')
        response = self.client.post(reverse('admin_profile_approvals'), {
            'action': 'approve',
            'request_id': req.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'approved')
        
        # Verify request updated
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        
        # Verify profile updated
        self.student_user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.student_user.first_name, 'Approved Name')
        self.assertEqual(self.student_user.email, 'approved@example.com')
        self.assertEqual(self.student.phone, '0987654321')

    def test_admin_rejects_profile_update(self):
        from .models import ProfileUpdateRequest
        req = ProfileUpdateRequest.objects.create(
            student=self.student,
            name='Rejected Name',
            email='rejected@example.com',
            phone='0987654321',
            status='pending'
        )
        # Login as admin
        self.client.login(username='admin_test', password='password123')
        response = self.client.post(reverse('admin_profile_approvals'), {
            'action': 'reject',
            'request_id': req.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'rejected')
        
        # Verify request rejected
        req.refresh_from_db()
        self.assertEqual(req.status, 'rejected')
        
        # Verify profile NOT updated
        self.student_user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.student_user.first_name, '')
        self.assertEqual(self.student_user.email, 'student@example.com')
        self.assertEqual(self.student.phone, '1234567890')

    def test_student_cannot_access_approvals_view(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('admin_profile_approvals'))
        # Should redirect to student dashboard
        self.assertRedirects(response, reverse('dashboard'))


    def test_admin_profile_get_unauthenticated(self):
        response = self.client.get(reverse('admin_profile'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('admin_profile'))

    def test_admin_profile_get_authenticated(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('admin_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/profile.html')
        self.assertContains(response, 'admin_test')
        self.assertContains(response, 'admin@example.com')

    def test_admin_profile_post_update(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.post(reverse('admin_profile'), {
            'username': 'admin_updated',
            'email': 'admin_updated@example.com',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin profile updated successfully.')
        
        # Verify db updates
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.username, 'admin_updated')
        self.assertEqual(self.admin_user.email, 'admin_updated@example.com')
        from django.contrib.auth.hashers import check_password
        self.assertTrue(check_password('newpassword123', self.admin_user.password))

    def test_login_unregistered_redirect(self):
        response = self.client.post(reverse('login'), {
            'username': 'non_existent_user',
            'password': 'somepassword'
        })
        self.assertRedirects(response, reverse('register') + '?unregistered=1')

    def test_register_page_unregistered_msg(self):
        response = self.client.get(reverse('register') + '?unregistered=1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have not registered. Please register first.')

    def test_student_model_properties(self):
        # Verify Student has name, email, and phone
        self.assertEqual(self.student.name, '')
        self.assertEqual(self.student.email, 'student@example.com')
        self.assertEqual(self.student.phone, '1234567890')
        
        # Test setter properties
        self.student.name = 'New Student Name'
        self.student.email = 'new_student@example.com'
        
        self.assertEqual(self.student.name, 'New Student Name')
        self.assertEqual(self.student.email, 'new_student@example.com')
        
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.first_name, 'New Student Name')
        self.assertEqual(self.student_user.email, 'new_student@example.com')

    def test_subject_and_question_models(self):
        from .models import Subject, Question
        
        # Create Subject
        subj = Subject.objects.create(name='Python Programming', description='Core Python concepts.')
        self.assertEqual(str(subj), 'Python Programming')
        self.assertEqual(subj.name, 'Python Programming')
        self.assertEqual(subj.description, 'Core Python concepts.')
        
        # Create Question
        q1 = Question.objects.create(subject=subj, question_text='What is a list comprehension in Python?')
        self.assertEqual(q1.subject, subj)
        self.assertEqual(q1.question_text, 'What is a list comprehension in Python?')
        self.assertEqual(str(q1), 'Python Programming: What is a list comprehension in Python?')
        
        # Verify Subject to Question relationship (Subject 1 --- * Question)
        q2 = Question.objects.create(subject=subj, question_text='How to declare a generator in Python?')
        self.assertEqual(subj.questions.count(), 2)
        
        # Verify Cascade delete behavior
        subj_id = subj.id
        q1_id = q1.id
        subj.delete()
        
        self.assertFalse(Subject.objects.filter(id=subj_id).exists())
        self.assertFalse(Question.objects.filter(id=q1_id).exists())

    def test_question_validation_empty_text(self):
        from .models import Subject, Question
        from django.core.exceptions import ValidationError
        
        subj = Subject.objects.create(name='Physics')
        q = Question(subject=subj, question_text='')
        with self.assertRaises(ValidationError):
            q.full_clean()


class QuestionManagementFlowTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from .models import Subject, Question
        
        # Create subjects
        self.math_subj = Subject.objects.create(name='Mathematics', description='Math related questions.')
        self.science_subj = Subject.objects.create(name='Science', description='Science related questions.')
        
        # Create a question
        self.question = Question.objects.create(subject=self.math_subj, question_text='What is 2 + 2?')
        
        # Create users
        self.admin_user = User.objects.create_superuser(username='admin_test', email='admin@example.com', password='password123')
        self.student_user = User.objects.create_user(username='student_test', email='student@example.com', password='password123')
        from .models import Student
        self.student = Student.objects.create(user=self.student_user, phone='1234567890')

    def test_unauthenticated_cannot_access_questions(self):
        response = self.client.get(reverse('question_list'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('question_list'))
        
        response_add = self.client.get(reverse('question_add'))
        self.assertRedirects(response_add, reverse('login') + '?next=' + reverse('question_add'))

    def test_student_cannot_access_questions(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('question_list'))
        self.assertRedirects(response, reverse('dashboard'))
        
        response_add = self.client.get(reverse('question_add'))
        self.assertRedirects(response_add, reverse('dashboard'))

    def test_admin_can_view_question_list(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('question_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/question_list.html')
        self.assertContains(response, 'Mathematics')
        self.assertContains(response, 'What is 2 + 2?')

    def test_admin_can_add_question_valid(self):
        self.client.login(username='admin_test', password='password123')
        
        # GET request
        response_get = self.client.get(reverse('question_add'))
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, 'adminpanel/question_form.html')
        self.assertContains(response_get, 'Add Question')
        
        # POST request
        response_post = self.client.post(reverse('question_add'), {
            'subject': self.science_subj.id,
            'question_text': 'What is H2O?'
        }, follow=True)
        self.assertRedirects(response_post, reverse('question_list'))
        self.assertContains(response_post, 'Question added successfully.')
        
        # Check database
        from .models import Question
        self.assertTrue(Question.objects.filter(question_text='What is H2O?').exists())

    def test_admin_add_question_invalid(self):
        self.client.login(username='admin_test', password='password123')
        
        # Empty question text
        response = self.client.post(reverse('question_add'), {
            'subject': self.math_subj.id,
            'question_text': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/question_form.html')
        self.assertContains(response, 'Question text is required.')
        
        # Missing subject
        response_sub = self.client.post(reverse('question_add'), {
            'subject': '',
            'question_text': 'Valid question text?'
        })
        self.assertEqual(response_sub.status_code, 200)
        self.assertTemplateUsed(response_sub, 'adminpanel/question_form.html')
        self.assertContains(response_sub, 'Subject is required.')

    def test_admin_can_edit_question_valid(self):
        self.client.login(username='admin_test', password='password123')
        
        # GET request
        response_get = self.client.get(reverse('question_edit', args=[self.question.id]))
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, 'adminpanel/question_form.html')
        self.assertContains(response_get, 'Edit Question')
        self.assertContains(response_get, 'What is 2 + 2?')
        
        # POST request
        response_post = self.client.post(reverse('question_edit', args=[self.question.id]), {
            'subject': self.science_subj.id,
            'question_text': 'What is gravity?'
        }, follow=True)
        self.assertRedirects(response_post, reverse('question_detail', args=[self.question.id]))
        self.assertContains(response_post, 'Question updated successfully.')
        
        # Check database
        self.question.refresh_from_db()
        self.assertEqual(self.question.subject, self.science_subj)
        self.assertEqual(self.question.question_text, 'What is gravity?')

    def test_admin_can_delete_question(self):
        self.client.login(username='admin_test', password='password123')
        
        response = self.client.post(reverse('question_delete', args=[self.question.id]), follow=True)
        self.assertRedirects(response, reverse('question_list'))
        self.assertContains(response, 'Question deleted successfully.')
        
        from .models import Question
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_admin_can_add_question_by_subject_name(self):
        self.client.login(username='admin_test', password='password123')
        
        # Post request with subject name string
        response = self.client.post(reverse('question_add'), {
            'subject': 'Science',
            'question_text': 'What is the speed of light?'
        }, follow=True)
        self.assertRedirects(response, reverse('question_list'))
        
        # Check database
        from .models import Question
        q = Question.objects.get(question_text='What is the speed of light?')
        self.assertEqual(q.subject, self.science_subj)

    def test_admin_can_add_new_subject_on_the_fly(self):
        self.client.login(username='admin_test', password='password123')
        
        # Post request with new subject name
        response = self.client.post(reverse('question_add'), {
            'subject': 'Geography',
            'question_text': 'What is the capital of France?'
        }, follow=True)
        self.assertRedirects(response, reverse('question_list'))
        
        # Check database for subject creation
        from .models import Subject, Question
        self.assertTrue(Subject.objects.filter(name='Geography').exists())
        subj = Subject.objects.get(name='Geography')
        q = Question.objects.get(question_text='What is the capital of France?')
        self.assertEqual(q.subject, subj)

    def test_admin_can_add_multiple_questions_at_once(self):
        self.client.login(username='admin_test', password='password123')
        
        # Post request with multiple lines
        questions_input = "Question One?\nQuestion Two?\nQuestion Three?"
        response = self.client.post(reverse('question_add'), {
            'subject': 'Mathematics',
            'question_text': questions_input
        }, follow=True)
        self.assertRedirects(response, reverse('question_list'))
        
        # Check database
        from .models import Question
        self.assertTrue(Question.objects.filter(question_text=questions_input).exists())
        self.assertEqual(Question.objects.filter(subject=self.math_subj).count(), 2) # 1 original + 1 multi-line question

    def test_admin_can_view_question_detail(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('question_detail', args=[self.question.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/question_detail.html')
        self.assertContains(response, 'Mathematics')
        self.assertContains(response, 'What is 2 + 2?')

    def test_student_cannot_access_question_detail(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('question_detail', args=[self.question.id]))
        self.assertRedirects(response, reverse('dashboard'))





