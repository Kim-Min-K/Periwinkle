from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import FollowRequest, Authors, Follow
from django.shortcuts import get_object_or_404
from accounts.serializers import authorSerializer, FollowRequestSerializer, FollowSerializer
from django.db import transaction
import uuid
'''
@api_view(['GET'])
def getAuthors(request)
'''