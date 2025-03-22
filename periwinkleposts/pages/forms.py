from django import forms
from django.forms import ModelForm
from api.models import ExternalNode

class AddNode(ModelForm):
    class Meta:
        model = ExternalNode
        fields = ['nodeURL', 'username', 'password', 'team_name']