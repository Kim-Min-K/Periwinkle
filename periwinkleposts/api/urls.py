from django.urls import path
from . import follow_views
from api.viewsets import FollowersViewSet, FollowRequestViewSet, AuthorViewSet, FolloweesViewSet
from accounts.views import CommentView, LikeView, InboxView
from rest_framework.routers import DefaultRouter
app_name = 'api'  

urlpatterns = [
    path('authors/<uuid:author_serial>/inbox', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<uuid:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers'),
    path('authors/', AuthorViewSet.as_view({'get': 'list'}), name='get-authors'),
    path('authors/<uuid:row_id>', AuthorViewSet.as_view({'get': 'retrieve'}), name=''),
    path('authors/<uuid:author_serial>/followees/<path:fqid>/unfollow', FolloweesViewSet.as_view({'post': 'unfollow'}), name='unfollow'),
    #----------Comments API ---------------------------------
    # ://service/api/authors/{AUTHOR_SERIAL}/inbox 
    path("authors/<uuid:author_serial>/inbox/", InboxView.as_view(), name="inbox"),
    # ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}/comments
    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/comments/",
        CommentView.as_view({'get': 'get_post_comments'}), name='get_post_comments' ),
    # ://service/api/posts/{POST_FQID}/comments
    path("posts/<str:post_fqid>/comments/", 
        CommentView.as_view({'get': 'known_post_comments'}), name = 'known_post_comments'),
    #----------Commented API------------------------------
    # Create a comment, api tested 
    path("authors/<uuid:author_serial>/commented/",
        CommentView.as_view({'get': 'all_comments', 'post':'create'}), name = 'createComment'),
    path("authors/<uuid:author_serial>/commented/<uuid:comment_serial>/", 
        CommentView.as_view({'get': 'retrieve'}), name="getComment"),
    

    # Liking a Post
    path("authors/<uuid:author_serial>/posts/<str:post_serial>/like/", 
        LikeView.as_view({'post': 'like_post'}), name="likePost"),

    # Liking a Comment
    path("authors/<uuid:author_serial>/comments/<str:comment_serial>/like/", 
        LikeView.as_view({'post': 'like_comment'}), name="likeComment"),

    # Get all comment list 
    path('authors/comments/', CommentView.as_view({'get': 'comment_list'}), name = 'commentList')
]
