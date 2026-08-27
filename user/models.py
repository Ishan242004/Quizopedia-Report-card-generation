from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

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
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
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

    def __str__(self):
        return f"{self.subject.name}: {self.question_text[:50]}"


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



