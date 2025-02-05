from django.contrib.auth.models import AbstractUser
from django.db import models

class Authors(AbstractUser):
    github_username = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username