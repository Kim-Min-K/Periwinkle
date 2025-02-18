from django.urls import path
from . import follow_views
from api.viewsets import FollowersViewSet

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', follow_views.followRequest, name='followRequest'),
    path('authors/<str:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers')
]