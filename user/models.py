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

