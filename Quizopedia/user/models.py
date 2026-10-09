from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import secrets

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username if self.user else "Student"

    @property
    def username(self):
        return self.user.username if self.user else ""

    @property
    def name(self):
        return self.user.first_name if self.user else ""

    @name.setter
    def name(self, value):
        if self.user:
            self.user.first_name = value
            if not self.user._state.adding:
                self.user.save()

    @property
    def email(self):
        return self.user.email if self.user else ""

    @email.setter
    def email(self, value):
        if self.user:
            self.user.email = value
            if not self.user._state.adding:
                self.user.save()

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        if user:
            user.delete()


class ProfileUpdateRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='profile_updates')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Update for {self.student.user.username} - {self.status}"


class Subject(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('qna', 'Question & Answer'),
        ('mcq', '4 Option MCQ'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPE_CHOICES, default='qna')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255, default="")
    option_b = models.CharField(max_length=255, default="")
    option_c = models.CharField(max_length=255, default="")
    option_d = models.CharField(max_length=255, default="")
    correct_option = models.CharField(
        max_length=1,
        choices=[('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')],
        default='A'
    )

    @property
    def is_mcq(self):
        return self.question_type == 'mcq'

    @property
    def is_qna(self):
        return self.question_type == 'qna'

    @property
    def correct_answer_text(self):
        """Returns the text of the correct answer."""
        answer_map = {'A': self.option_a, 'B': self.option_b, 'C': self.option_c, 'D': self.option_d}
        return answer_map.get(self.correct_option, self.option_a)

    def sync_options(self):
        """Syncs legacy options fields (option_a..d) with Option model instances."""
        if self.question_type == 'mcq' and (self.option_a or self.option_b):
            options_data = [
                (self.option_a, self.correct_option == 'A'),
                (self.option_b, self.correct_option == 'B'),
                (self.option_c, self.correct_option == 'C'),
                (self.option_d, self.correct_option == 'D'),
            ]
            existing_options = list(self.options.order_by('id'))
            if len(existing_options) == 4:
                for opt, (text, is_ans) in zip(existing_options, options_data):
                    if opt.option_text != text or opt.is_answer != is_ans:
                        opt.option_text = text
                        opt.is_answer = is_ans
                        opt.save()
            else:
                self.options.all().delete()
                for text, is_ans in options_data:
                    if text:
                        self.options.create(option_text=text, is_answer=is_ans)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.question_type == 'mcq' and (self.option_a or self.option_b):
            self.sync_options()

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.subject.name}: {self.question_text[:50]}"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)
    is_answer = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.option_text} ({'Correct' if self.is_answer else 'Incorrect'})"


class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='report_cards')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='report_cards')
    total_questions = models.IntegerField()
    attempted_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    wrong_answers = models.IntegerField()
    total_marks = models.IntegerField()
    obtained_marks = models.IntegerField()
    percentage = models.FloatField()
    result_grade = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report Card: {self.student.user.username} - {self.subject.name}"


class StudentOTP(models.Model):
    """
    Model storing one-time passwords (OTP) with expiration for student authentication.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student OTP'
        verbose_name_plural = 'Student OTPs'

    def __str__(self):
        return f"OTP for {self.student.user.username} (Used: {self.is_used})"

    @classmethod
    def generate_otp_code(cls):
        """Generates a cryptographically secure 6-digit numeric string preserving leading zeros."""
        return f"{secrets.randbelow(1000000):06d}"

    @property
    def is_expired(self):
        """Returns True if the current timezone-aware time is at or beyond the expiration timestamp."""
        return timezone.now() >= self.expires_at

    def is_valid(self):
        """Returns True if the OTP is unexpired and has not been used."""
        return not self.is_used and not self.is_expired



