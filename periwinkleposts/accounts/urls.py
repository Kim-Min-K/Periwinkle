from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import authorAPI

app_name = "accounts"

urlpatterns = [
<<<<<<< HEAD
    path('register/', views.registerView, name='register'),
    path('login/', views.loginView, name='login'),
    path('profile/<str:username>/', views.profileView, name='profile'),
=======
    path("register/", views.registerView, name="register"),
    path("login/", views.loginView, name="login"),
    path("profile/", views.profileView, name="profile"),
    path("home/", views.homePageView, name="home"),
>>>>>>> af77fa1 (home page for all posts)
]

router = DefaultRouter()
router.register(r"users", authorAPI)

# I used https://www.geeksforgeeks.org/how-to-create-a-basic-api-using-django-rest-framework/ to do the api stuff

apipatterns = [
    path("api/", include(router.urls)),
    path("api/profile/", authorAPI.as_view({"get": "profile"}), name="api-profile"),
]

urlpatterns += apipatterns
