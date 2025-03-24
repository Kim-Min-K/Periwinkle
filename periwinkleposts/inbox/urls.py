from django.urls import path
from . import views

urlpatterns = [
    path('authors/<uuid:author_id>/inbox/', views.inbox_view, name='inbox'),
]