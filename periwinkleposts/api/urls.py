from django.urls import path, include
from api.viewsets import *
from accounts.views import CommentView, LikeView, InboxView
from rest_framework.routers import DefaultRouter
from api.views import NodeAuthCheckView

app_name = 'api'  

urlpatterns = [
    path('authors/', AuthorViewSet.as_view({'get': 'list'}), name='getAuthors'),
    path('authors/<uuid:row_id>', AuthorViewSet.as_view({'get': 'retrieve', 'put':'update'}), name='getAuthor'),
    #----------Comments API ---------------------------------
    # Get all comment objects,for testing purpose only
    path('authors/comments/', CommentView.as_view({'get': 'comment_list'}), name = 'commentList'),
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
    # ://service/api/authors/{AUTHOR_SERIAL}/commented 
    path("authors/<uuid:author_serial>/commented/",
        CommentView.as_view({'get': 'all_comments', 'post':'create'}), name = 'createComment'),
    # ://service/api/authors/{AUTHOR_FQID}/commented 
    path("authors/<path:author_fqid>/commented/", 
        CommentView.as_view({'get': 'author_commented'}), name="author_commented"),
    # ://service/api/authors/{AUTHOR_SERIAL}/commented/{COMMENT_SERIAL} 
    path("authors/<uuid:author_serial>/commented/<uuid:comment_serial>/", 
        CommentView.as_view({'get': 'retrieve'}), name="getComment"),   
    #://service/api/commented/{COMMENT_FQID}
    path("commented/<path:comment_fqid>/",
        CommentView.as_view({'get': 'get_comment_by_fqid'}),name='get_comment_by_fqid'),

    #----------For create like------------------------------
    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/like/", 
        LikeView.as_view({'post': 'like_post'}), name="likePost"),
    # Liking a Comment
    path("authors/<uuid:author_serial>/comments/<uuid:comment_serial>/like/", 
        LikeView.as_view({'post': 'like_comment'}), name="likeComment"),
    #----------Likes API------------------------------
    # ://service/api/authors/{AUTHOR_SERIAL}/inbox
    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/likes/", 
        LikeView.as_view({'get': 'get_post_likes'}), name="get_post_likes"),
    # ://service/api/posts/{POST_FQID}/likes
    path("posts/<path:post_fqid>/likes/", 
        LikeView.as_view({'get': 'get_all_post_likes'}), name="get_all_post_likes"),
    # ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}/comments/{COMMENT_FQID}/likes
    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/comments/<path:comment_fqid>/likes/",
        LikeView.as_view({'get': 'get_comment_likes'}), name = "get_comment_likes"),

    #----------Liked API------------------------------
    # ://service/api/authors/{AUTHOR_SERIAL}/liked
    path("authors/<uuid:author_serial>/liked",
        LikeView.as_view({'get': 'get_author_likes'}), name = 'get_author_likes'),
    # ://service/api/authors/{AUTHOR_SERIAL}/liked/{LIKE_SERIAL}
    path("authors/<uuid:author_serial>/liked/<like_serial>/",
        LikeView.as_view({'get':'get_single_like'}), name = 'get_single_like'),
    # ://service/api/authors/{AUTHOR_FQID}/liked
    path("authors/<path:author_fqid>.liked/",
        LikeView.as_view({'get': 'get_like_by_author_fqid'}), name="get_like_by_author_fqid"),
    # ://service/api/liked/{LIKE_FQID}
    path('liked/<path:like_fqid>/',
        LikeView.as_view({'get': 'a_single_like'}), name = 'a_single_like'),
    #-----------POST API--------------------------------
    path('authors/<uuid:author_serial>/posts/', PostViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='author-posts'),
    
    path('authors/<uuid:author_serial>/posts/<uuid:id>', PostViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='post-detail'),
    
    path('posts/', PostViewSet.as_view({'get': 'list_all'}), name='all-posts'),
    
    path('posts/<path:post_fqid>', PostViewSet.as_view({
        'get': 'get_by_fqid'
    }), name='post-by-fqid'),

    #---------Inbox--------------
    # ://service/api/authors/{AUTHOR_SERIAL}/inbox, for comment, follow and like
    path("authors/<uuid:author_serial>/inbox/", InboxView.as_view(), name="inbox"),
    #-------Auth?--------
    path("auth-check/", NodeAuthCheckView.as_view(), name="node-auth-check"),
]


follow_request_patterns = [
    path('authors/<uuid:author_serial>/follow-requests', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<uuid:author_serial>/follow-requests/incoming', FollowRequestViewSet.as_view({'get': 'getFollowRequests'}), name='getFollowRequestIn'),
    path('authors/<uuid:author_serial>/follow-requests/outgoing', FollowRequestViewSet.as_view({'get': 'getOutGoingFollowRequests'}), name='getFollowRequestOut'),
    path('authors/<uuid:author_serial>/follow-requests/incoming/author/<uuid:requester_serial>/accept', FollowRequestViewSet.as_view({'post': 'acceptFollowRequest'}), name='acceptFollowRequest'),
    path('authors/<uuid:author_serial>/follow-requests/incoming/author/<uuid:requester_serial>/decline', FollowRequestViewSet.as_view({'post': 'declineFollowRequest'}), name='declineFollowRequest'),
    path('authors/<uuid:author_serial>/follow-requests/suggestions', FollowRequestViewSet.as_view({'get': 'getRequestSuggestions'}), name='getRequestSuggestions'),
]

followees_patterns = [
    path('authors/<uuid:author_serial>/followees/<path:fqid>/unfollow', FolloweesViewSet.as_view({'post': 'unfollow'}), name='unfollow'),
    path('authors/<uuid:author_serial>/followees', FolloweesViewSet.as_view({'get': 'getFollowees'}), name='getFollowees'),
]

followers_patterns = [
    path('authors/<uuid:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers'),
    path('authors/<uuid:author_serial>/followers/<path:foreign_author_fqid>', FollowersViewSet.as_view({'get': 'isFollower'}), name="isFollower")
]

friends_patterns = [
    path('authors/<uuid:author_serial>/friends', FriendsViewSet.as_view({'get': 'getFriends'}), name='getFriends'),
]

urlpatterns += follow_request_patterns
urlpatterns += followees_patterns
urlpatterns += followers_patterns
urlpatterns += friends_patterns
