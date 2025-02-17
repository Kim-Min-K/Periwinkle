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

@api_view(['GET'])
def getFriends(request, author_serial):

    try:
        # Convert the serial string to a UUID object if your IDs are UUIDs
        author_uuid = uuid.UUID(author_serial)
    except ValueError:
        return Response({'error': 'Invalid UUID format.'}, status=400)

    # Retrieve the author for whom we want to get friends
    author = get_object_or_404(Authors, pk=author_uuid)

    # Get all authors that this author follows (i.e., followees)
    following_ids = Follow.objects.filter(follower=author).values_list('followee_id', flat=True)
    
    # Get all authors that follow this author (i.e., followers)
    followers_ids = Follow.objects.filter(followee=author).values_list('follower_id', flat=True)

    # The friends are the intersection of the two sets
    friend_ids = list(set(following_ids).intersection(set(followers_ids)))

    # Retrieve the friend Author objects
    friends = Authors.objects.filter(row_id__in=friend_ids)

    # Serialize the friend objects
    serializer = authorSerializer(friends, many=True)

    return Response({
        "type":"friends",
        "friends": serializer.data
    })

@api_view(['GET'])
def getFollowRequests(request, author_serial):
    try:
        author_uuid = uuid.UUID(author_serial)
    except ValueError:
        return Response({'error': 'Invalid UUID format.'}, status=400)

    author = get_object_or_404(Authors, pk=author_uuid)

    requesters_ids = FollowRequest.objects.filter(requestee=author).values_list('requester_id', flat=True)

    requesters = Authors.objects.filter(row_id__in=requesters_ids)

    # Serialize the friend objects
    serializer = authorSerializer(requesters, many=True)
    
    return Response({
        "type":"requesters",
        "requesters": serializer.data
    }, status=200)

@api_view(['GET'])
def getSuggestions(request, author_serial):
    try:
        # Convert the provided author_serial (assumed to be a UUID string) into a UUID object
        author_uuid = uuid.UUID(author_serial)
    except ValueError:
        return Response({'error': 'Invalid UUID format.'}, status=400)

    # Retrieve the current author
    current_author = get_object_or_404(Authors, row_id=author_uuid)
    
    # Get a list of row_ids for authors that the current author is already following
    followed_ids = Follow.objects.filter(follower=current_author)\
                                  .values_list('followee__row_id', flat=True)
    
    # Get 5 authors that the current author is NOT following
    # Also, exclude the current author from the suggestions
    suggestions = Authors.objects.exclude(row_id__in=followed_ids)\
                                 .exclude(row_id=current_author.row_id)\
                                 .order_by('?')[:5]
    
    # Serialize the suggestions using the authorSerializer
    serializer = authorSerializer(suggestions, many=True)

    return Response({
        "type":"suggestions",
        "suggestions": serializer.data
    }, status=200)

