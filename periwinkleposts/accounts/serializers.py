from rest_framework import serializers
from .models import Authors, Follow, FollowRequest

def required(value):
    print(value)
    if value is None or value == '':
        raise serializers.ValidationError('This field is required.')

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff 

class authorSerializer(serializers.ModelSerializer):

    host = serializers.CharField(
        required=True, 
        min_length=23,
        validators=[required]
    )

    class Meta:
        model = Authors
        fields = ['row_id', 'id', 'host', 'username', 'email', 'github_username']
        extra_kwargs = {
            'host': {'required': True, 'allow_blank': False}
        }

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

class FollowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowRequest
        fields = ['requestee', 'requester', 'requested_since']
        # This example assumes you have a unique constraint at the model level, e.g.:
        # unique_together = ('requester', 'requestee')