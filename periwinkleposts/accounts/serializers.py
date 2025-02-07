from rest_framework import serializers
from .models import Authors

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff 

class authorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = ['id', 'username', 'email', 'github_username']