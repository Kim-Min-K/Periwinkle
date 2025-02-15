from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Authors

class AuthorCreation(UserCreationForm):
    github_username = forms.CharField(max_length=100, required=False)
    host = forms.CharField(max_length=200, required=True)
    class Meta:
        model = Authors
        fields = ("username", "host", "github_username", "password1", "password2")