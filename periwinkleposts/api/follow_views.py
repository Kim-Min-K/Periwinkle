from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import FollowRequest, Authors, Follow
from django.shortcuts import get_object_or_404
from accounts.serializers import FollowRequestSerializer, FollowSerializer
from api.serializers import AuthorSerializer
from django.db import transaction
import uuid
from api.serializers import AuthorSerializer

# Create your views here.

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
def getSuggestions(request, author_serial):
    try:
        # Convert the provided author_serial (assumed to be a UUID string) into a UUID object
        if type(author_serial) == str:
            author_uuid = author_serial
        else:
            author_uuid = author_serial
            
    except ValueError:
        return Response({'error': 'Invalid UUID format.'}, status=400)

    # Retrieve the current author
    current_author = get_object_or_404(Authors, row_id=author_uuid)
    
    # Get a list of row_ids for authors that the current author is already following
    followed_ids = Follow.objects.filter(follower=current_author)\
                                  .values_list('followee__row_id', flat=True)

    request_ids = FollowRequest.objects.filter(requester=current_author).values_list("requestee__row_id", flat=True)
    
    # Get 5 authors that the current author is NOT following
    # Also, exclude the current author from the suggestions
    suggestions = Authors.objects.exclude(row_id__in=followed_ids)\
                                 .exclude(row_id=current_author.row_id)\
                                 .exclude(row_id__in=request_ids)\
                                 .exclude(is_staff=1)\
                                 .order_by('?')[:5]
    
    # Serialize the suggestions using the authorSerializer
    serializer = AuthorSerializer(suggestions, many=True, context={'request': request})

    return Response({
        "type":"suggestions",
        "suggestions": serializer.data
    }, status=200)

def getSentRequests(request, author_serial):
    try:
        author_uuid = author_serial  # Convert string to UUID
    except ValueError:
        return Response({'error': 'Invalid UUID format'}, status=400)

    requestees = FollowRequest.objects.filter(requester=author_uuid)

    requestee_ids = [connection.requestee for connection in requestees]

    requestee_serializer = AuthorSerializer(requestee_ids, many=True, context={'request': request})

    return Response({
        "type": "sent_requests",
        "sent_requests": requestee_serializer.data  # Include followers' data
    }, status=200)
