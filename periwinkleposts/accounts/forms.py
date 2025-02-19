from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Authors

class AuthorCreation(UserCreationForm):
    github_username = forms.CharField(max_length=100, required=False)
    host = forms.CharField(max_length=200, required=True)
    class Meta:
        model = Authors
        fields = ("username", "host", "github_username", "password1", "password2")
        
# simple form that defines what model to alter and what field
class AvatarUpload(forms.ModelForm):
    class Meta:
        model = Authors
        fields = ["avatar", "avatar_url"]  # Both are model fields
        widgets = {
            'avatar_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 bg-white rounded-lg border-2 border-[#d9d9d9] text-[15px] font-normal placeholder:text-black placeholder:opacity-30 focus:outline-none focus:border-[#8A8AFF]',
                'placeholder': 'Provide a link instead'
            }),
        }

    # jesus christ this fix took forever. some boolean stuff to make sure the form is cleaned and overwrites work.
    def clean(self):
        cleaned_data = super().clean()
        avatar = cleaned_data.get('avatar')
        avatar_url = cleaned_data.get('avatar_url')
        current_avatar = self.instance.avatar if self.instance else None

        new_avatar = (
            avatar and 
            (not current_avatar or avatar != current_avatar)
        ) # check if avatar exists, and that avatar isnt the same as the current one
        
        new_url = (
            avatar_url and 
            avatar_url != self.instance.avatar_url
        )

        if new_avatar and new_url:
            raise forms.ValidationError("Choose only one: file or URL")
        if not new_avatar and not new_url:
            raise forms.ValidationError("No changes detected")

        return cleaned_data
    
class EditProfile(forms.ModelForm):
    class Meta:
        model = Authors
        fields = ['username', 'email', 'displayName', 'github_username']