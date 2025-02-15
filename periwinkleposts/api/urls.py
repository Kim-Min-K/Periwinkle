from django.urls import path
from . import views

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', views.followRequest, name='followRequest'),
]