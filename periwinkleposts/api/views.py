from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import FollowRequest, Authors
from django.shortcuts import get_object_or_404
from accounts.serializers import authorSerializer, FollowRequestSerializer
from django.db import transaction
import uuid

# Create your views here.

@api_view(['POST'])
def followRequest(request, author_serial):
    try:
        with transaction.atomic():
            print(request.build_absolute_uri("/"))
            followee_author = get_object_or_404(Authors, pk=uuid.UUID(hex=author_serial))
            follower = request.data.get("actor")
            del follower["id"]
            follower_serializer = authorSerializer(data=follower, partial=True)
            if not follower_serializer.is_valid():
                raise ValueError(follower_serializer.errors)
            follower_author = follower_serializer.save()
            follow_request_serializer = FollowRequestSerializer(data={"requestee":followee_author.id, "requester":follower_author.id}, partial=True)
            if not follow_request_serializer.is_valid():
                raise ValueError(follow_request_serializer.errors)
            follow_request_serializer.save()
    except ValueError as e:
        # Return the validation error message
        return Response({"error": str(e)}, status=400)
    return Response(status=200)