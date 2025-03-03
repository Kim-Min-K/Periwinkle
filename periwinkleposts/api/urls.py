from django.urls import path
from . import follow_views
from api.viewsets import FollowersViewSet, FollowRequestViewSet, AuthorViewSet
from api.authorViews import getAuthors, getAuthorDetail
from accounts.views import CommentView, LikeView
app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<str:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers'),
    path('authors/', AuthorViewSet.as_view({'get': 'list'}), name='get-authors'),
    path('authors/<str:row_id>', getAuthorDetail.as_view(), name=''),
    

    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/comments/", 
         CommentView.as_view({'post': 'create'}), name="createComment"),

    # Liking a Post
    path("authors/<uuid:author_serial>/posts/<uuid:post_serial>/like/", 
        LikeView.as_view({'post': 'like_post'}), name="likePost"),

    # Liking a Comment
    path("authors/<uuid:author_serial>/comments/<uuid:comment_serial>/like/", 
        LikeView.as_view({'post': 'like_comment'}), name="likeComment"),
]