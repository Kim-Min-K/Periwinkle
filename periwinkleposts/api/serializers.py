from accounts.serializers import *
from accounts.models import *
from rest_framework.decorators import action
from django.urls import reverse
from .models import *

class AuthorSerializer(serializers.Serializer):
    type = serializers.CharField(default="author")
    row_id = serializers.UUIDField(default="row.id")
    id = serializers.CharField()
    host = serializers.SerializerMethodField()
    displayName = serializers.CharField(source="username") #do we want to keep username and display seperate?
    github = serializers.SerializerMethodField()
    profileImage = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()

    def get_id(self, obj):
        request = self.context.get('request')
        host = request.build_absolute_uri('/api/authors/')
        return f"{host}{obj.row_id}"

    def get_host(self, obj):
        request = self.context.get('request')
        host = request.build_absolute_uri('/api/')
        return f"{host}"
    
    def get_github(self, obj):
        return f"https://github.com/{obj.github_username}"

    def get_profileImage(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return obj.avatar_url

    def get_page(self, obj):
        return self.context['request'].build_absolute_uri(f'/accounts/profile/{obj.username}') # this should be changed to UUID

class AuthorObjectToJSONSerializer(serializers.Serializer):
    type = serializers.CharField(default="author")
    id = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    displayName = serializers.CharField() #do we want to keep username and display seperate?
    github = serializers.SerializerMethodField()
    profileImage = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.id

    def get_host(self, obj):
        return obj.host
    
    def get_github(self, obj):
        return f"https://github.com/{obj.github_username}"

    def get_profileImage(self, obj):
        print("Hey")
        if obj.avatar:
            print("Yo")
            print(obj.host[:-5] + str(obj.avatar.url))
            return obj.host[:-5] + str(obj.avatar.url)
        return obj.avatar_url


    def get_displayName(self, obj):
        return obj.displayName

    def get_page(self, obj):
        return obj.host[:-5] + (f'/accounts/profile/{obj.row_id}') # this should be changed to UUID

class FollowersSerializer(serializers.Serializer):
    type = serializers.CharField(default="followers", read_only=True)
    followers = AuthorObjectToJSONSerializer(many=True)

class AuthorsSerializer(serializers.Serializer):
    type = serializers.CharField(default="authors")
    authors = AuthorSerializer(many=True)

class PostSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="post", read_only=True)
    id = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    contentType = serializers.CharField()
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'type', 'title', 'id', 'page', 'description', 'contentType',
            'content', 'author', 'comments', 'likes', 'published', 'visibility',
            'image', 'image_url', 'video' 
        ]
        extra_kwargs = {
            'image_url': {'write_only': True}  # hides in response
        }

    def get_id(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse('api:post-detail', args=[obj.author.row_id, obj.id])
        )

    def get_page(self, obj):
        request = self.context.get('request')
        return f"{request.build_absolute_uri('/')}authors/{obj.author.username}/posts/{obj.id}"

    def get_author(self, obj):
        return AuthorSerializer(obj.author, context=self.context).data

    def get_comments(self, obj):
        request = self.context.get('request')
        comments = obj.comments.filter(post=obj).order_by('-published')[:5]
        return {
            "type": "comments",
            "page": self.get_page(obj),
            "id": f"{self.get_id(obj)}/comments",
            "page_number": 1,
            "size": 5,
            "count": obj.comments.count(),
            "src": CommentSerializer(
                comments,
                many=True,
                context={'request': request}
            ).data
        }

    def get_likes(self, obj):
        request = self.context.get('request')
        likes = obj.likes.filter(post=obj).order_by('-published')[:50]
        return {
            "type": "likes",
            "page": f"{self.get_page(obj)}/likes",
            "id": f"{self.get_id(obj)}/likes",
            "page_number": 1,
            "size": 50,
            "count": obj.likes.count(),
            "src": LikeSerializer(
                likes,
                many=True,
                context={'request': request}
            ).data
        }
        
    def get_image(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return obj.image_url

    def get_video(self, obj):
        if obj.video:
            return self.context['request'].build_absolute_uri(obj.video.url)
        return None

class NodeSerializer(serializers.Serializer):
    nodeURL = serializers.URLField()
    username = serializers.CharField()
    password = serializers.CharField()
    team_name = serializers.CharField()
    
    class Meta:
        model = ExternalNode
        fields = ['nodeURL', 'username', 'password', 'team_name']
    