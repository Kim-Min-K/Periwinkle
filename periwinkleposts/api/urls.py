from django.urls import path
from . import follow_views
from api.viewsets import FollowersViewSet, FollowRequestViewSet, AuthorViewSet
from accounts.views import CommentView, LikeView
from rest_framework.routers import DefaultRouter
app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<str:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers'),
    path('authors/', AuthorViewSet.as_view({'get': 'list'}), name='get-authors'),
    path('authors/<uuid:row_id>', AuthorViewSet.as_view({'get': 'retrieve'}), name=''),
    
    # Create a comment
    path("authors/<str:author_serial>/commented/",
         CommentView.as_view({'get': 'all_comments', 'post':'create'}), name = 'createComment'),
    # path("authors/<str:author_serial>/posts/<str:post_serial>/comments/", 
    #     CommentView.as_view({'post': 'create'}), name="createComment"),
    
    
    path("authors/<str:author_serial>/commented/<uuid:comment_serial>/", 
        CommentView.as_view({'get': 'retrieve'}), name="getComment"),

    # Liking a Post
    path("authors/<str:author_serial>/posts/<str:post_serial>/like/", 
        LikeView.as_view({'post': 'like_post'}), name="likePost"),

    # Liking a Comment
    path("authors/<str:author_serial>/comments/<str:comment_serial>/like/", 
        LikeView.as_view({'post': 'like_comment'}), name="likeComment"),

    # Get all comment list 
    path('authors/comments/', CommentView.as_view({'get': 'comment_list'}), name = 'commentList')
]
