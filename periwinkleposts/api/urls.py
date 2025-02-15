from django.urls import path
from . import views

app_name = 'pages'  

urlpatterns = [
    path('authors/<int:author_serial>/inbox', views.followRequest, name='followRequest'),
]