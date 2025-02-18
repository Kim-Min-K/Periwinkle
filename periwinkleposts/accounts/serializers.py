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

    def to_representation(self, instance):

        followers = Follow.objects.filter(followee=instance.row_id)  # Get all followers

        # Get the list of followers by extracting the `follower` field from each Follow object
        follower_ids = [connection.follower for connection in followers]

        follower_serializer = authorSerializer(follower_ids, many=True)  # Serialize multiple followers

        res = {
            "type":"followers",
            "followers":follower_serializer.data
        }
        print("To Representation " + str(res))
        return res
    
# class FollowRequestSerializerRaw(serializers.Serializer):
#     type = serializers.CharField(required=False, default="follow")
#     summary = serializers.CharField(required=False)
#     actor = authorSerializer()
#     object = authorSerializer(required=False)

#     def create(self, validated_data):
#         actor_data = validated_data.get("actor")
#         object_data = validated_data.get("object")

#         # Compute default summary if not provided.
#         summary = validated_data.get("summary")
#         if not summary:
#             # Use 'displayName' if available, otherwise fallback to 'username'
#             actor_username = actor_data.get("username")
#             object_username = object_data.get("username")
#             summary = f"{actor_username} wants to follow {object_username}"
#             validated_data["summary"] = summary

#         with transaction.atomic():
#                 try:
#                     requester = Authors.objects.get(id=actor_data.get("id"))
#                 except Authors.DoesNotExist:
#                     requester_serializer = authorSerializer(data=actor_data)
#                     requester_serializer.is_valid(raise_exception=True)
#                     requester = requester_serializer.save()
                
#                 # Get or create the requestee (object)
#                 try:
#                     requestee = Authors.objects.get(id=object_data.get("id"))
#                 except Authors.DoesNotExist:
#                     requestee_serializer = authorSerializer(data=object_data)
#                     requestee_serializer.is_valid(raise_exception=True)
#                     requestee = requestee_serializer.save()
#                 follow_request_serializer = FollowRequestSerializer(data={"followee":requestee.row_id,"follower":requester.row_id})
                
#                 if not follow_request_serializer.is_valid():
#                     raise ValueError(follow_request_serializer.errors)
#                 #Create the FollowRequest instance
#                 follow_request = follow_request_serializer.save()
#         return follow_request

#     def to_representation(self, instance):
#         actor_data = authorSerializer(instance.requester).data
#         object_data = authorSerializer(instance.requestee).data

#         rep = {
#             "type": "follow",
#             "summary": instance.summary if instance.summary else f"{actor_data.get('username')} wants to follow {object_data.get('username')}",
#             "actor": actor_data,
#             "object": object_data
#         }
#         return rep