from django.db import models
from accounts.models import Authors

# Create your models here.
class Inbox(models.Model):
    author = models.ForeignKey(Authors, on_delete=models.CASCADE)
    items = models.JSONField(default=list)