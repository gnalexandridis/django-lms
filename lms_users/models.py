from django.contrib.auth.models import AbstractUser
from django.db import models


class Roles(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    TEACHER = "TEACHER", "Teacher"


class User(AbstractUser):
    # Keep email optional and non-unique; identity is by username
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(
        max_length=16,
        choices=Roles.choices,
        default=Roles.STUDENT,
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self):
        return self.username
