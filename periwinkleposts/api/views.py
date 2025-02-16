from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import FollowRequest, Authors
from django.shortcuts import get_object_or_404
from accounts.serializers import authorSerializer, FollowRequestSerializer, FollowSerializer
from django.db import transaction
import uuid

# Create your views here.

@api_view(['POST'])
def followRequest(request, author_serial):
    try:
        with transaction.atomic():

            requestee = get_object_or_404(Authors, pk=uuid.UUID(hex=author_serial))
            requester_json = request.data.get("actor")

            # Use requester object in database if it exists otherwise create it
            try:
                requester = Authors.objects.get(id=requester_json["id"])
            except Authors.DoesNotExist:
                requester_serializer = authorSerializer(data=requester_json)
                if not requester_serializer.is_valid():
                    raise ValueError(requester_serializer.errors)
                requester = requester_serializer.save()
                
            follow_request_serializer = FollowRequestSerializer(data={"requestee":requestee.row_id, "requester":requester.row_id}, partial=True)
            if not follow_request_serializer.is_valid():
                raise ValueError(follow_request_serializer.errors)
            follow_request_serializer.save()

    except ValueError as e:
        # Return the validation error message
        return Response({"error": str(e)}, status=400)

    return Response({"message":"Follow request successfuly sent."}, status=200)

@api_view(['PUT'])
def acceptFollowRequest(request, request_id):
    try:
        with transaction.atomic():
            request = get_object_or_404(FollowRequest, pk=request_id)
            follow_serializer = FollowSerializer(data={"followee": request.requestee.row_id, "follower": request.requester.row_id})
            if not follow_serializer.is_valid():
                raise ValueError(follow_serializer.errors)
            follow_serializer.save()
            request.delete()
    except ValueError as e:
        # Return the validation error message
        return Response({"error": str(e)}, status=400)
    return Response({"message": "Follow request successfully accepted."}, status=200)