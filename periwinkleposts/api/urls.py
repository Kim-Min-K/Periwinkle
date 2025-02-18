from django.urls import path
from . import follow_views
from api.viewsets import FollowersViewSet, FollowRequestViewSet

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<str:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers')
]