from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import FollowRequest, Authors, Follow
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

@api_view(['DELETE'])
def declineFollowRequest(request, request_id):
    try:
        with transaction.atomic():
            request = get_object_or_404(FollowRequest, pk=request_id)
            request.delete()
    except ValueError as e:
        # Return the validation error message
        return Response({"error": str(e)}, status=400)
    return Response({"message": "Follow request successfully accepted."}, status=200)


@api_view(['GET'])
def getFollowers(request, author_serial):
    try:
        author_uuid = uuid.UUID(hex=author_serial)  # Convert string to UUID
    except ValueError:
        return Response({'error': 'Invalid UUID format'}, status=400)

    followers = Follow.objects.filter(followee=author_uuid)  # Get all followers

    # Get the list of followers by extracting the `follower` field from each Follow object
    follower_ids = [connection.follower for connection in followers]

    follower_serializer = authorSerializer(follower_ids, many=True)  # Serialize multiple followers

    return Response({
        "type": "followers",
        "followers": follower_serializer.data  # Include followers' data
    }, status=200)