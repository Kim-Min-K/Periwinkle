from django.urls import path, include, re_path
from . import views
from rest_framework.routers import DefaultRouter
from .views import authorAPI, create_post, delete_post,CommentView, LikeView

app_name = "accounts"

urlpatterns = [
    path("register/", views.registerView, name="register"),
    path("login/", views.loginView, name="login"),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path("profile/<path:row_id>/", views.profileView, name="profile"),
    path("avatar/", views.uploadAvatar, name="avatar"),
    path("create-post/", create_post, name="create_post"),
    path("post/delete/<uuid:post_id>/", delete_post, name="delete_post"),
    path('approval-pending/', views.approval_pending, name='approval_pending'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('edit_post/<uuid:post_id>/', views.edit_post, name='edit_post'),
    path(
        "authors/<uuid:author_serial>/follow-requests/incoming/author/<uuid:requester_serial>/accept",
        views.acceptRequest,
        name="acceptRequest",
    ),
    path(
        "authors/<uuid:author_serial>/follow-requests/incoming/author/<uuid:requester_serial>/decline",
        views.declineRequest,
        name="declineRequest",
    ),
    path(
        "authors/<uuid:author_serial>/follow-requests", views.sendFollowRequest, name="sendFollowRequest"
    ),
    path("authors/<uuid:author_serial>/followees/<path:fqid>/unfollow", views.unfollow, name="unfollow"),

    # View a Specific Post via URL
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/', views.view_post, name='view_post'),
   
]
router = DefaultRouter()
# router.register(r"users", authorAPI)
# router.register(r"comments", CommentView)
# router.register(r"likes", LikeView)

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff

apipatterns = [
    path("api/", include(router.urls)),
    path("api/profile/", authorAPI.as_view({"get": "profile"}), name="api-profile"),

]

urlpatterns += apipatterns
