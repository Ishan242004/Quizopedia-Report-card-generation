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
        self.assertTrue('Registration Successful!' in response.content.decode() or 'Account Created!' in response.content.decode())
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
        
        # Create Question (default type is 'qna')
        q1 = Question.objects.create(subject=subj, question_text='What is a list comprehension in Python?')
        self.assertEqual(q1.subject, subj)
        self.assertEqual(q1.question_text, 'What is a list comprehension in Python?')
        self.assertEqual(q1.question_type, 'qna')
        self.assertEqual(str(q1), '[Question & Answer] Python Programming: What is a list comprehension in Python?')
        
        # Create MCQ Question
        q_mcq = Question.objects.create(
            subject=subj,
            question_type='mcq',
            question_text='Which is a list?',
            option_a='[]', option_b='{}', option_c='()', option_d='<>',
            correct_option='A'
        )
        self.assertEqual(q_mcq.question_type, 'mcq')
        self.assertTrue(q_mcq.is_mcq)
        self.assertFalse(q_mcq.is_qna)
        self.assertEqual(q_mcq.correct_answer_text, '[]')
        
        # Verify Subject to Question relationship (Subject 1 --- * Question)
        q2 = Question.objects.create(subject=subj, question_text='How to declare a generator in Python?')
        self.assertEqual(subj.questions.count(), 3)
        
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
        # Question list now shows subjects as cards, not individual question text
        self.assertContains(response, 'Mathematics')

    def test_admin_can_add_question_valid(self):
        self.client.login(username='admin_test', password='password123')
        
        # GET request — now shows type selection page
        response_get = self.client.get(reverse('question_add'))
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, 'adminpanel/question_type_select.html')
        self.assertContains(response_get, 'Add Question')
        
        # Add Q&A question via the new Q&A add form
        response_qna = self.client.post(reverse('question_add_qna'), {
            'subject': 'Science',
            'question_text': 'What is H2O?',
            'answer': 'Water'
        }, follow=True)
        self.assertEqual(response_qna.status_code, 200)
        self.assertContains(response_qna, 'Question added successfully.')
        
        # Check database
        from .models import Question
        q = Question.objects.get(question_text='What is H2O?')
        self.assertEqual(q.question_type, 'qna')
        self.assertEqual(q.option_a, 'Water')
        self.assertEqual(q.subject, self.science_subj)

    def test_admin_add_question_invalid(self):
        self.client.login(username='admin_test', password='password123')
        
        # Empty question text on Q&A add
        response = self.client.post(reverse('question_add_qna'), {
            'subject': 'Mathematics',
            'question_text': '',
            'answer': 'Some answer'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/question_add_qna.html')
        self.assertContains(response, 'Question text is required.')
        
        # Missing subject on Q&A add
        response_sub = self.client.post(reverse('question_add_qna'), {
            'subject': '',
            'question_text': 'Valid question text?',
            'answer': 'Some answer'
        })
        self.assertEqual(response_sub.status_code, 200)
        self.assertTemplateUsed(response_sub, 'adminpanel/question_add_qna.html')
        self.assertContains(response_sub, 'Subject is required.')

    def test_admin_can_edit_question_valid(self):
        self.client.login(username='admin_test', password='password123')
        
        # GET request — question is Q&A type (default), should show Q&A edit template
        response_get = self.client.get(reverse('question_edit', args=[self.question.id]))
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, 'adminpanel/question_edit_qna.html')
        self.assertContains(response_get, 'Edit Question')
        self.assertContains(response_get, 'What is 2 + 2?')
        
        # POST request — edit Q&A question
        response_post = self.client.post(reverse('question_edit', args=[self.question.id]), {
            'subject': 'Science',
            'question_text': 'What is gravity?',
            'answer': 'A force',
        }, follow=True)
        self.assertRedirects(response_post, reverse('question_detail', args=[self.question.id]))
        self.assertContains(response_post, 'Question updated successfully.')
        
        # Check database
        self.question.refresh_from_db()
        self.assertEqual(self.question.subject, self.science_subj)
        self.assertEqual(self.question.question_text, 'What is gravity?')
        self.assertEqual(self.question.option_a, 'A force')
        self.assertEqual(self.question.question_type, 'qna')

    def test_admin_can_delete_question(self):
        self.client.login(username='admin_test', password='password123')
        
        subject_id = self.question.subject.id
        response = self.client.post(reverse('question_delete', args=[self.question.id]), follow=True)
        # Delete now redirects to subject_questions instead of question_list
        self.assertRedirects(response, reverse('subject_questions', args=[subject_id]))
        self.assertContains(response, 'Question deleted successfully.')
        
        from .models import Question
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_admin_can_delete_entire_quiz(self):
        self.client.login(username='admin_test', password='password123')
        from .models import Subject, Question
        
        subj = Subject.objects.create(name='Temporary Subject')
        q1 = Question.objects.create(subject=subj, question_text='Temp Q1')
        q2 = Question.objects.create(subject=subj, question_text='Temp Q2')
        
        subj_id = subj.id
        q1_id = q1.id
        q2_id = q2.id
        
        response = self.client.post(reverse('subject_delete', args=[subj_id]), follow=True)
        self.assertRedirects(response, reverse('question_list'))
        self.assertContains(response, "Temporary Subject")
        self.assertContains(response, "and all its questions deleted successfully.")
        
        self.assertFalse(Subject.objects.filter(id=subj_id).exists())
        self.assertFalse(Question.objects.filter(id=q1_id).exists())
        self.assertFalse(Question.objects.filter(id=q2_id).exists())

    def test_admin_can_add_question_by_subject_name(self):
        self.client.login(username='admin_test', password='password123')
        
        # Post request with subject name via Q&A add
        response = self.client.post(reverse('question_add_qna'), {
            'subject': 'Science',
            'question_text': 'What is the speed of light?',
            'answer': '3 x 10^8 m/s'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check database
        from .models import Question
        q = Question.objects.get(question_text='What is the speed of light?')
        self.assertEqual(q.subject, self.science_subj)

    def test_admin_can_add_new_subject_on_the_fly(self):
        self.client.login(username='admin_test', password='password123')
        
        # Post request with new subject name via Q&A add
        response = self.client.post(reverse('question_add_qna'), {
            'subject': 'Geography',
            'question_text': 'What is the capital of France?',
            'answer': 'Paris'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check database for subject creation
        from .models import Subject, Question
        self.assertTrue(Subject.objects.filter(name='Geography').exists())
        subj = Subject.objects.get(name='Geography')
        q = Question.objects.get(question_text='What is the capital of France?')
        self.assertEqual(q.subject, subj)
        self.assertEqual(q.question_type, 'qna')

    def test_admin_can_add_multiple_questions_at_once(self):
        self.client.login(username='admin_test', password='password123')
        
        # Post request with multiple MCQ questions via MCQ bulk add
        questions_input = "Q1. Question One?\nA) Option A1\nB) Option B1\nC) Option C1\nD) Option D1\nCorrect Answer: A\n\nQ2. Question Two?\nA) Option A2\nB) Option B2\nC) Option C2\nD) Option D2\nCorrect Answer: A"
        response = self.client.post(reverse('question_add_mcq'), {
            'subject': 'Mathematics',
            'mcq_text': questions_input
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check database
        from .models import Question
        self.assertTrue(Question.objects.filter(question_text='Question One?').exists())
        self.assertTrue(Question.objects.filter(question_text='Question Two?').exists())
        # 1 existing + 2 new MCQ = 3 total for math subject
        self.assertEqual(Question.objects.filter(subject=self.math_subj).count(), 3)
        # Verify they're MCQ type
        q1 = Question.objects.get(question_text='Question One?')
        self.assertEqual(q1.question_type, 'mcq')
        self.assertEqual(q1.option_a, 'Option A1')
        self.assertEqual(q1.correct_option, 'A')

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


class OptionModelFlowTests(TestCase):
    def setUp(self):
        from .models import Subject, Question, Option
        self.Subject = Subject
        self.Question = Question
        self.Option = Option
        self.subject = Subject.objects.create(name='Computer Science')

    def test_option_model_creation(self):
        """Test creating Option with question ForeignKey, option_text, and is_answer."""
        question = self.Question.objects.create(
            subject=self.subject,
            question_text='What is CPU?',
            question_type='mcq'
        )
        opt1 = self.Option.objects.create(question=question, option_text='Central Processing Unit', is_answer=True)
        opt2 = self.Option.objects.create(question=question, option_text='Central Power Unit', is_answer=False)

        self.assertEqual(opt1.question, question)
        self.assertEqual(opt1.option_text, 'Central Processing Unit')
        self.assertTrue(opt1.is_answer)
        self.assertFalse(opt2.is_answer)
        self.assertEqual(question.options.count(), 2)

    def test_question_cascade_delete_options(self):
        """Deleting a question must cascade delete its options."""
        question = self.Question.objects.create(
            subject=self.subject,
            question_text='Sample Question?',
            question_type='mcq'
        )
        self.Option.objects.create(question=question, option_text='Option 1', is_answer=False)
        self.Option.objects.create(question=question, option_text='Option 2', is_answer=True)
        self.assertEqual(self.Option.objects.filter(question=question).count(), 2)

        question_id = question.id
        question.delete()
        self.assertEqual(self.Option.objects.filter(question_id=question_id).count(), 0)

    def test_mcq_backward_compatibility_sync(self):
        """MCQ question created with option_a..d automatically syncs with Option model."""
        q_mcq = self.Question.objects.create(
            subject=self.subject,
            question_type='mcq',
            question_text='Which language is used for Django?',
            option_a='Python',
            option_b='Java',
            option_c='C++',
            option_d='Ruby',
            correct_option='A',
        )
        options = list(q_mcq.options.order_by('id'))
        self.assertEqual(len(options), 4)
        self.assertEqual(options[0].option_text, 'Python')
        self.assertTrue(options[0].is_answer)
        self.assertEqual(options[1].option_text, 'Java')
        self.assertFalse(options[1].is_answer)


class SampleReportCardQuizDataTests(TestCase):
    def test_populate_sample_quiz_data_command(self):
        """Verify populate_sample_quiz_data creates 3 subjects, 6 questions, 4 options each, exactly 1 answer."""
        from django.core.management import call_command
        from .models import Subject, Question, Option

        call_command('populate_sample_quiz_data')

        expected_subjects = ['Python Programming', 'Mathematics', 'Computer Science']
        sample_subjects = Subject.objects.filter(name__in=expected_subjects)

        # 1. Subject count for these sample subjects = 3
        self.assertEqual(sample_subjects.count(), 3)

        total_questions = 0
        total_options = 0

        for subj in sample_subjects:
            # 2. Every subject has exactly 2 questions
            questions = Question.objects.filter(subject=subj)
            self.assertEqual(questions.count(), 2)
            total_questions += questions.count()

            for q in questions:
                # Question type is mcq
                self.assertEqual(q.question_type, 'mcq')

                # 3. Every question has exactly 4 options in the new Option model
                options = Option.objects.filter(question=q).order_by('id')
                self.assertEqual(options.count(), 4)
                total_options += options.count()

                # 4. Every question has exactly 1 option where is_answer=True
                correct_options = options.filter(is_answer=True)
                self.assertEqual(correct_options.count(), 1)

                # 5. Legacy MCQ fields match Option records
                letter_map = {'A': q.option_a, 'B': q.option_b, 'C': q.option_c, 'D': q.option_d}
                correct_opt_obj = correct_options.first()
                self.assertEqual(correct_opt_obj.option_text, letter_map[q.correct_option])

        # 6. Question count created by this task = 6
        self.assertEqual(total_questions, 6)
        # 7. Total option count = 24
        self.assertEqual(total_options, 24)

    def test_sample_quiz_attempt_generates_report_card(self):
        """Verify that attempting a quiz on sample subject generates a valid ReportCard."""
        from django.core.management import call_command
        from .models import Subject, Question, Student, ReportCard
        from django.contrib.auth.models import User

        call_command('populate_sample_quiz_data')

        user = User.objects.create_user(username='test_student_quiz', email='quiz@example.com', password='password123')
        student = Student.objects.create(user=user, phone='9876543210')
        self.client.login(username='test_student_quiz', password='password123')

        subject = Subject.objects.get(name='Python Programming')
        questions = Question.objects.filter(subject=subject).order_by('id')
        self.assertEqual(questions.count(), 2)

        # Submit quiz answers matching the correct options
        post_data = {
            f"question_{questions[0].id}": questions[0].correct_option,
            f"question_{questions[1].id}": questions[1].correct_option,
        }
        response = self.client.post(reverse('quiz_attempt', args=[subject.id]), post_data)

        # Should redirect to report card view
        self.assertEqual(response.status_code, 302)

        # Verify ReportCard
        report_card = ReportCard.objects.filter(student=student, subject=subject).first()
        self.assertIsNotNone(report_card)
        self.assertEqual(report_card.total_questions, 2)
        self.assertEqual(report_card.attempted_questions, 2)
        self.assertEqual(report_card.correct_answers, 2)
        self.assertEqual(report_card.wrong_answers, 0)
        self.assertEqual(report_card.percentage, 100.0)
        self.assertEqual(report_card.result_grade, 'A')






