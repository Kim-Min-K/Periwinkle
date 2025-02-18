from rest_framework import serializers
from .models import Authors, Follow, FollowRequest
from django.db import transaction

def required(value):
    if value is None or value == '':
        raise serializers.ValidationError('This field is required.')

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff 

class authorSerializer(serializers.ModelSerializer):

    host = serializers.CharField(
        required=True,
        validators=[required]
    )

    class Meta:
        model = Authors
        fields = ['row_id', 'id', 'host', 'displayName', 'username', 'email', 'github_username']
        extra_kwargs = {
            'host': {'required': True, 'allow_blank': False}
        }
    
    def to_representation(self, instance):
        # Get the default representation from the superclass
        representation = super().to_representation(instance)

        del representation["row_id"]
        
        return representation

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['followee', 'follower', 'followed_since']

    def to_representation(self, instance):
        # Get the default representation from the superclass
        representation = super().to_representation(instance)
        
        return representation
        
class FollowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowRequest
        fields = ['requestee', 'requester', 'requested_since']
        # This example assumes you have a unique constraint at the model level, e.g.:
        # unique_together = ('requester', 'requestee')

class FollowersSerializer(serializers.Serializer):
    type = serializers.CharField(default="followers")
    followers = authorSerializer(many=True)
    
class FollowRequestSerializerRaw(serializers.Serializer):
    type = serializers.CharField(default="follow")
    summary = serializers.CharField(default=None)
    actor = authorSerializer()
    object = authorSerializer()