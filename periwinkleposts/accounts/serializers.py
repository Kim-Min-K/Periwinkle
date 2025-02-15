from rest_framework import serializers
from .models import Authors, Follow, FollowRequest

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff 

class authorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authors
        fields = ['row_id', 'username', 'email', 'github_username']

class FollowSerializer(serializers.Serializer):
    follower = serializers.PrimaryKeyRelatedField(queryset=Authors.objects.all())  # ForeignKey to question
    followee = serializers.PrimaryKeyRelatedField(queryset=Authors.objects.all())
    followed_since = serializers.DateTimeField()  # Timestamp of follow action

    def create(self, validated_data):
        """
        Create and return a new `Follow` instance, given the validated data
        """
        return Follow.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Follow` instance, given the validated data
        """
        instance.save()
        return instance

class FollowRequestSerializer(serializers.Serializer):
    requestee = serializers.PrimaryKeyRelatedField(queryset=Authors.objects.all())
    requester = serializers.PrimaryKeyRelatedField(queryset=Authors.objects.all())
    requested_since = serializers.DateTimeField()

    def create(self, validated_data):
        """
        Create and return a new `FollowRequest` instance, given the validated data
        """
        return FollowRequest.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `FollowRequest` instance, given the validated data
        """
        instance.save()
        return instance