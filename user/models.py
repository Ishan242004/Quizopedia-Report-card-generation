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
    def email(self):
        return self.user.email if self.user else ""

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        if user:
            user.delete()

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    total_marks = models.IntegerField(default=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Quizzes"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')])
    marks = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}"

class StudentAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username if self.student.user else 'Student'} - {self.quiz.title} ({self.score})"

class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='report_cards')
    attempt = models.OneToOneField(StudentAttempt, on_delete=models.CASCADE, related_name='report_card', null=True, blank=True)
    grade = models.CharField(max_length=5)
    remarks = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report Card: {self.student.user.username if self.student.user else 'Student'} - Grade {self.grade}"
