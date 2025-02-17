from django.urls import path
from . import follow_views

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', follow_views.followRequest, name='followRequest'),
    path('authors/<str:author_serial>/followers', follow_views.getFollowers, name='getFollowers'),
    # path('authors/<str:author_serial>/suggestions', views.getSuggestions, name='getSuggestions')
]