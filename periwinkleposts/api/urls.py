from django.urls import path
from . import views

app_name = 'api'  

urlpatterns = [
    path('authors/<str:author_serial>/inbox', views.followRequest, name='followRequest'),
    path('follow-requests/<int:request_id>/accept', views.acceptFollowRequest, name="acceptFollowRequest"),
    path('follow-requests/<int:request_id>/decline', views.declineFollowRequest, name="declineFollowRequest")
]