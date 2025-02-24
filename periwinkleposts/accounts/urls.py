from django.urls import path, include, re_path
from . import views
from rest_framework.routers import DefaultRouter
from .views import authorAPI, create_post, delete_post,CommentView, LikeView

app_name = "accounts"

urlpatterns = [
    path("register/", views.registerView, name="register"),
    path("login/", views.loginView, name="login"),
    path("profile/<str:username>", views.profileView, name="profile"),
    path(
        "authors/<str:author_serial>/followers/<path:fqid>/accept",
        views.acceptRequest,
        name="acceptRequest",
    ),
    path(
        "authors/<str:author_serial>/followers/<path:fqid>/decline",
        views.declineRequest,
        name="declineRequest",
    ),
    path(
        "authors/<path:fqid>/inbox", views.sendFollowRequest, name="sendFollowRequest"
    ),
    path("avatar/", views.uploadAvatar, name="avatar"),
    path("create-post/", create_post, name="create_post"),
    path("post/delete/<uuid:post_id>/", delete_post, name="delete_post"),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('approval-pending/', views.approval_pending, name='approval_pending'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
]
router = DefaultRouter()
router.register(r"users", authorAPI)
router.register(r"comments", CommentView)
router.register(r"likes", LikeView)

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff

apipatterns = [
    path("api/", include(router.urls)),
    path("api/profile/", authorAPI.as_view({"get": "profile"}), name="api-profile"),
    # Comments API
    path("api/authors/<uuid:author_serial>/posts/<uuid:post_serial>/comments/", 
         CommentView.as_view({"get": "post_comments", "post": "create"}), name="post_comments"),
    # Likes API for posts
    path("api/authors/<uuid:author_serial>/posts/<uuid:post_serial>/likes/", 
         LikeView.as_view({"get": "post_likes", "post": "like_post"}), name="post_likes"),
    # Likes API for comments
    path("api/authors/<uuid:author_serial>/comments/<uuid:comment_serial>/likes/", 
         LikeView.as_view({"get": "comment_likes", "post": "like_comment"}), name="comment_likes"),
]

urlpatterns += apipatterns
