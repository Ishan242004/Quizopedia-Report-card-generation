from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from user.models import Student, ProfileUpdateRequest
import io
import sys


class ProfileApprovalEmailTests(TestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@quizopedia.com',
            password='AdminPassword123!'
        )

        # Create a regular student user
        self.student_user = User.objects.create_user(
            username='rohan_student',
            first_name='Rohan',
            email='rohan.old@example.com',
            password='StudentPassword123!'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            phone='9876543210'
        )

    def test_approve_profile_request_sends_email_and_prints_terminal(self):
        """Admin approving profile update sends confirmation email and updates student info."""
        req = ProfileUpdateRequest.objects.create(
            student=self.student,
            name='Rohan Sharma',
            email='rohan.new@example.com',
            phone='9999888877',
            status='pending'
        )

        self.client.login(username='admin_test', password='AdminPassword123!')

        # Capture terminal stdout
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured_output
            response = self.client.post(reverse('admin_profile_approvals'), {
                'action': 'approve',
                'request_id': req.id
            }, follow=True)
        finally:
            sys.stdout = old_stdout

        terminal_text = captured_output.getvalue()

        # Verify redirect and success message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'approved and applied')

        # Check database update
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.student_user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.student_user.first_name, 'Rohan Sharma')
        self.assertEqual(self.student_user.email, 'rohan.new@example.com')
        self.assertEqual(self.student.phone, '9999888877')

        # Check terminal output
        self.assertIn('[EMAIL NOTIFICATION - PROFILE APPROVED]', terminal_text)
        self.assertIn('rohan.new@example.com', terminal_text)
        self.assertIn('Rohan Sharma', terminal_text)

        # Check email sent via django mail system
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn('Approved', sent_email.subject)
        self.assertIn('rohan.new@example.com', sent_email.to)
        self.assertIn('Rohan Sharma', sent_email.body)
        self.assertIn('9999888877', sent_email.body)

    def test_reject_profile_request_sends_email_and_prints_terminal(self):
        """Admin rejecting profile update sends rejection email with reason and does not modify student info."""
        req = ProfileUpdateRequest.objects.create(
            student=self.student,
            name='Fake Name',
            email='fake@example.com',
            phone='1111222233',
            status='pending'
        )

        self.client.login(username='admin_test', password='AdminPassword123!')

        # Capture terminal stdout
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured_output
            response = self.client.post(reverse('admin_profile_approvals'), {
                'action': 'reject',
                'request_id': req.id,
                'rejection_reason': 'Identity documents could not be verified.'
            }, follow=True)
        finally:
            sys.stdout = old_stdout

        terminal_text = captured_output.getvalue()

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'has been rejected')

        # Check database status
        req.refresh_from_db()
        self.assertEqual(req.status, 'rejected')
        self.assertEqual(req.rejection_reason, 'Identity documents could not be verified.')

        # Existing student profile must remain unchanged
        self.student_user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.student_user.first_name, 'Rohan')
        self.assertEqual(self.student_user.email, 'rohan.old@example.com')
        self.assertEqual(self.student.phone, '9876543210')

        # Check terminal output
        self.assertIn('[EMAIL NOTIFICATION - PROFILE REJECTED / CANCELLED]', terminal_text)
        self.assertIn('Identity documents could not be verified.', terminal_text)

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn('Rejected', sent_email.subject)
        self.assertIn('rohan.old@example.com', sent_email.to)
        self.assertIn('Identity documents could not be verified.', sent_email.body)
        self.assertIn('Fake Name', sent_email.body)

    def test_dashboard_quick_approval_sends_email(self):
        """Quick approval from admin dashboard also triggers email notification."""
        req = ProfileUpdateRequest.objects.create(
            student=self.student,
            name='Rohan Quick',
            email='rohan.quick@example.com',
            phone='9111222333',
            status='pending'
        )

        self.client.login(username='admin_test', password='AdminPassword123!')

        response = self.client.post(reverse('admin_dashboard'), {
            'action': 'approve',
            'request_id': req.id
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Approved', mail.outbox[0].subject)
        self.assertIn('rohan.quick@example.com', mail.outbox[0].to)
