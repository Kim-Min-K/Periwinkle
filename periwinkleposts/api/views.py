from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import FollowRequest

# Create your views here.

@api_view(['POST'])
def followRequest(request, author_serial):
    print("Hi")
    return Response(status=200)