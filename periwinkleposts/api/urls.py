from django.urls import path, include
from api.viewsets import *
from accounts.views import CommentView, LikeView, InboxView
from rest_framework.routers import DefaultRouter
app_name = 'api'  

urlpatterns = [
    path('authors/<uuid:author_serial>/follow-requests', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<uuid:author_serial>/follow-requests/incoming', FollowRequestViewSet.as_view({'get': 'getFollowRequests'}), name='getFollowRequestIn'),
    path('authors/<uuid:author_serial>/follow-requests/outgoing', FollowRequestViewSet.as_view({'get': 'getOutGoingFollowRequests'}), name='getFollowRequestOut'),
    path('authors/<uuid:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers'),
    path('authors/<uuid:author_serial>/followees/<path:fqid>/unfollow', FolloweesViewSet.as_view({'post': 'unfollow'}), name='unfollow'),
    path('authors/<uuid:author_serial>/followees', FolloweesViewSet.as_view({'get': 'getFollowees'}), name='getFollowees'),
    path('authors/<uuid:author_serial>/friends', FriendsViewSet.as_view({'get': 'getFriends'}), name='getFriends'),
    path('authors/<uuid:author_serial>/follow-requests/incoming/author/<uuid:requester_serial>/accept', FollowRequestViewSet.as_view({'post': 'acceptFollowRequest'}), name='acceptFollowRequest'),
    path('authors/<uuid:author_serial>/follow-requests/incoming/author/<uuid:requester_serial>/decline', FollowRequestViewSet.as_view({'post': 'declineFollowRequest'}), name='declineFollowRequest'),
    path('authors/<uuid:author_serial>/follow-requests/suggestions', FollowRequestViewSet.as_view({'get': 'getRequestSuggestions'}), name='getRequestSuggestions'),
    path('authors/', AuthorViewSet.as_view({'get': 'list'}), name='getAuthors'),
    path('authors/<uuid:row_id>', AuthorViewSet.as_view({'get': 'retrieve'}), name='getAuthor'),
    #----------Comments API ---------------------------------
    # Get all comment objects,for testing purpose only
    path('authors/comments/', CommentView.as_view({'get': 'comment_list'}), name = 'commentList'),
    # ://service/api/authors/{AUTHOR_SERIAL}/inbox 
    path("authors/<uuid:author_serial>/inbox/", InboxView.as_view(), name="inbox"),
    # ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}/comments
    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/comments/",
        CommentView.as_view({'get': 'get_post_comments'}), name='get_post_comments' ),
    # ://service/api/posts/{POST_FQID}/comments
    path("posts/<path:post_fqid>/comments/", 
        CommentView.as_view({'get': 'known_post_comments'}), name = 'known_post_comments'),
    # ://service/api/authors/{AUTHOR_SERIAL}/post/{POST_SERIAL}/comment/{REMOTE_COMMENT_FQID}
    path("authors/<uuid:author_serial>/post/<uuid:post_serial>/comment/<str:remote_comment_fqid>/",
        CommentView.as_view({'get': 'get_comment'}), name="get_comment"),
    #----------Commented API------------------------------
    # Create a comment, api tested 
    path("authors/<uuid:author_serial>/commented/",
        CommentView.as_view({'get': 'all_comments', 'post':'create'}), name = 'createComment'),
    # URL: ://service/api/authors/{AUTHOR_FQID}/commented
    path("authors/<uuid:author_serial>/commented/<uuid:comment_serial>/", 
        CommentView.as_view({'get': 'retrieve'}), name="getComment"),
    

    # Liking a Post
    path("authors/<uuid:author_serial>/posts/<str:post_serial>/like/", 
        LikeView.as_view({'post': 'like_post'}), name="likePost"),

    # Liking a Comment
    path("authors/<uuid:author_serial>/comments/<str:comment_serial>/like/", 
        LikeView.as_view({'post': 'like_comment'}), name="likeComment"),

    
    
    path('authors/<uuid:author_serial>/posts/', PostViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='author-posts'),
    
    path('authors/<uuid:author_serial>/posts/<uuid:id>', PostViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='post-detail'),
    
    path('posts/<path:post_fqid>', PostViewSet.as_view({
        'get': 'get_by_fqid'
    }), name='post-by-fqid'),
]
