from django.urls import path
from . import views

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', views.followRequest, name='followRequest'),
    path('authors/<str:author_serial>/followers', views.getFollowers, name='getFollowers'),
    # path('authors/<str:author_serial>/suggestions', views.getSuggestions, name='getSuggestions')
]