from django.urls import path
from . import follow_views
from api.viewsets import FollowersViewSet, FollowRequestViewSet, AuthorViewSet
from api.authorViews import getAuthors, getAuthorDetail

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', FollowRequestViewSet.as_view({'post': 'makeRequest'}), name='followRequest'),
    path('authors/<str:author_serial>/followers', FollowersViewSet.as_view({'get': 'list'}), name='getFollowers'),
    path('authors/', AuthorViewSet.as_view({'get': 'list'}), name='get-authors'),
    path('authors/<str:row_id>', getAuthorDetail.as_view(), name='')
    
]