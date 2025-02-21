from rest_framework import serializers
from .models import Authors, Follow, FollowRequest, Comment, Like
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

# ---------------------- Comment and Like ------------------------------------
'''
{
            "type":"comment",
            "author":{
                "type":"author",
                "id":"http://nodeaaaa/api/authors/111",
                "page":"http://nodeaaaa/authors/greg",
                "host":"http://nodeaaaa/api/",
                "displayName":"Greg Johnson",
                "github": "http://github.com/gjohnson",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            "comment":"Sick Olde English",
            "contentType":"text/markdown",
            // ISO 8601 TIMESTAMP
            "published":"2015-03-09T13:07:04+00:00",
            // ID of the Comment
            "id":"http://nodeaaaa/api/authors/111/commented/130",
            "post": "http://nodebbbb/api/authors/222/posts/249",
            // this may or may not be the same as page for the post,
            // depending if there's a seperate URL to just see the one comment in html
            "page": "http://nodebbbb/authors/222/posts/249"
            "likes:..............
}
'''
class CommentSerialier(serializers.ModelSerializer):
    type = serializers.CharField(default = 'comment', read_only = True)
    author = serializers.SerializerMethodField()
    comment = serializers.CharField()
    contentType = serializers.CharField(source = 'content_type')
    # https://www.django-rest-framework.org/api-guide/fields/#date-and-time-fields
    published = serializers.DateTimeField(read_only = True)
    # https://www.django-rest-framework.org/api-guide/fields/#serializermethodfield
    # To get the value by calling method
    id = serializers.SerializerMethodField()
    post = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['type','author', 'comment','contentType','published','id','post','likes']
    
    def get_id(self, obj):
        return f"{obj.author.id}/commented/{obj.id}"
    
    def get_post(self, obj):
        return f"{obj.post.author.id}/posts/{obj.post.id}"
    
    '''"
    author":{
                "type":"author",
                "id":"http://nodeaaaa/api/authors/111",
                "page":"http://nodeaaaa/authors/greg",
                "host":"http://nodeaaaa/api/",
                "displayName":"Greg Johnson",
                "github": "http://github.com/gjohnson",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
    '''
    def get_author(self, obj):
        author_obj = obj.author
        host_without_api = author_obj.host.rstrip("api/")
        return {
            "type": "author",
            "id": author_obj.id,
            "page": f"{host_without_api}/authors/{author_obj.username}",
            "host": {author_obj.host},
            "displayName": author_obj.displayName,
            "github": author_obj.github_username if author_obj.github_username else "",
            "profileImage": author_obj.avatar_display() or "",
        }

    '''
    "likes": {
                "type": "likes",
                "id": "http://nodeaaaa/api/authors/111/commented/130/likes",
                // in this example nodebbbb has a html page just for the likes
                "page": "http://nodeaaaa/authors/greg/comments/130/likes"
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": [],
            },'''
    def get_likes(self, obj):
        likes_list = obj.likes.order_by("published")
        total = len(likes_list)
        like_src = LikeSerializer(likes_list[:5], many = True).data
        host_without_api = obj.author.host.rstrip("api/")
        return {
            'type': 'likes',
            'id':   f"{obj.author.id}/commented/{obj.id}/likes",
            'page': f"{obj.author.id}/comments/{obj.id}/likes",
            "page_number": 1,
            "size": 50,
            "count": total,
            "src": like_src
        }
    # def create(self, validated_data):
        
    

'''{
    "type":"like",
    "author":{
        "type":"author",
        "id":"http://nodeaaaa/api/authors/111",
        "page":"http://nodeaaaa/authors/greg",
        "host":"http://nodeaaaa/api/",
        "displayName":"Greg Johnson",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
    },
    // ISO 8601 TIMESTAMP
    "published":"2015-03-09T13:07:04+00:00",
    "id":"http://nodeaaaa/api/authors/111/liked/166",
    // ID of the Comment (UUID)
    "object": "http://nodebbbb/api/authors/222/posts/249"
    //or "object": "http://nodeaaaa/api/authors/111/commented/130" for comment
}'''
class LikeSerializer(serializers.Serializer):
    type = serializers.CharField(default = 'like')
    author = serializers.SerializerMethodField()
    published = serializers.DateTimeField()
    id = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField

    class Meta:
        model = Like
        fileds = ['type', 'author','published','id','object']

    def get_id(self,obj):
        return f"{obj.author.id}/liked/{obj.id}"
    
    def get_object(self, obj):
        if obj.post:
            return f"{obj.post.author.id}/posts/{obj.post.id}"
        elif obj.comment:
            return f"{obj.comment.author.id}/commented/{obj.comment.id}"
        return None
    
    def get_author(self, obj):
        author_obj = obj.author
        host_without_api = author_obj.host.rstrip("api/")
        return {
            "type": "author",
            # "id": f"{author_obj.host}authors/{author_obj.id}",
            "id": author_obj.id,
            "page": f"{host_without_api}/authors/{author_obj.username}",
            "host": {author_obj.host},
            "displayName": author_obj.displayName,
            "github": author_obj.github_username if author_obj.github_username else "",
            "profileImage": author_obj.avatar_display() or "",
        }