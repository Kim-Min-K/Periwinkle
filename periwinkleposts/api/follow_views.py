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
