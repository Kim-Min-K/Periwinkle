from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from accounts.models import FollowRequest, Authors, Follow
from django.shortcuts import get_object_or_404
from accounts.serializers import authorSerializer, FollowRequestSerializer, FollowSerializer
from django.db import transaction
import uuid
from accounts.models import Authors
from django.core.paginator import Paginator
from api.viewsets import AuthorSerializer
''' EVERYTHING HERE IS DEPRECATED. LEAVING IT FOR REFERENCE. 
@api_view(['GET'])
def getAuthors(request):
    page_number = request.GET.get('page', 1)
    size = request.GET.get('size', 10)
    
    try:
        page_number = int(page_number)
        size = int(size)
    except ValueError:
        return Response({"error": "Invalid page or size parameters"}, status=400)

    authors = Authors.objects.all().order_by('id')
    
    paginator = Paginator(authors, size)
    try:
        page = paginator.page(page_number)
    except Exception:
        return Response({"Unknown Error"}, status=500)

    response_data = {
        "type": "authors",
        "authors": []
    }

    # Build base URLs
    base_url = request.build_absolute_uri('/api/')  # Host URL
    api_base = request.build_absolute_uri('/api/authors/')

    for author in page.object_list:
        # Build individual author URLs
        author_url = f"{api_base}{author.row_id}/"
        profile_page = f"{base_url.replace('/api/', '/')}accounts/{author.username}/"
        github = "https://github.com/" + author.github_username
        if author.avatar:
            profile_image = request.build_absolute_uri(author.avatar.url)
        else:
            profile_image = author.avatar_url

        author_data = {
            "type": "author",
            "id": author_url,
            "host": base_url,
            "displayName": author.username,
            "github": github,
            "profileImage": profile_image,
            "page": profile_page
        }
        response_data["authors"].append(author_data)

    return Response(response_data)
    
class getAuthorDetail(RetrieveAPIView):
    queryset = Authors.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = 'row_id'

'''