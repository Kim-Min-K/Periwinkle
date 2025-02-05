from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Authors

# so the replaced users still shows up in the auth panel
class AuthorsAdmin(UserAdmin):  
    list_display = ('username', 'email', 'is_staff', 'is_active', 'github_username')
    fieldsets = UserAdmin.fieldsets + ( 
        ('Additional Info', {'fields': ('github_username',)}),
    )

admin.site.register(Authors, AuthorsAdmin)