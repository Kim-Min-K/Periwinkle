from django.urls import path
from . import views

app_name = 'pages'  

urlpatterns = [
    path('home/', views.homeView, name='home'),
    path('nodereg/', views.nodeView, name='node')
]