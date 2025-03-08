from accounts.serializers import *
from accounts.models import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from drf_yasg import openapi
import uuid
from rest_framework.decorators import action
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import permissions
from django.urls import reverse
from api.serializers import *

class FollowersSerializer(serializers.Serializer):
    type = serializers.CharField(default="followers")
    followers = authorSerializer(many=True)
    
class FollowRequestSerializerRaw(serializers.Serializer):
    type = serializers.CharField(default="follow")
    summary = serializers.CharField(default=None)
    actor = authorSerializer()
    object = authorSerializer()

class FollowersViewSet(GenericViewSet):
    serializer_class=FollowersSerializer

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get the followers of an author",
        responses={200: serializer_class()}
    )
    def list(self, request, author_serial):
        try:
            author_uuid = author_serial  # Convert string to UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format'}, status=400)

        followers = Follow.objects.filter(followee=author_uuid)  # Get all followers

        # Get the list of followers by extracting the `follower` field from each Follow object
        follower_ids = [connection.follower for connection in followers]

        follower_serializer = authorSerializer(follower_ids, many=True)  # Serialize multiple followers

        res = {
            "type":"followers",
            "followers":follower_serializer.data
        }

        return Response(res)

class FolloweesViewSet(GenericViewSet):
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_description="Unfollow a followee of an author",
        responses={
            200: UnfollowSerializer(),
            404: "The author is not following the corresponding followee or one of the authors does not exist ."
            }
    )
    def unfollow(self, request, author_serial, fqid):
        try:
            author_uuid = author_serial  # Convert string to UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format'}, status=400)

        follower = get_object_or_404(Authors, row_id=author_uuid)
        followee = get_object_or_404(Authors, id=fqid)
        serializer = UnfollowSerializer(actor=follower, object=followee)
        data = serializer.to_representation()
        serializer.save()
        return Response(data, status=200)


class FollowRequestViewSet(GenericViewSet):
    serializer_class=FollowRequestSerializerRaw

    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_description="Send a follow request to an author.",
        responses={
            201: "Follow request successfully sent.",
            400: "Serializer errors. "
        }
    )
    def makeRequest(self, request, author_serial):
        try:
            with transaction.atomic():

                requestee = get_object_or_404(Authors, pk=author_serial)
                requester_json = request.data.get("actor")
                print(requester_json)

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
    
    
class AuthorViewSet(GenericViewSet):
    serializer_class = AuthorsSerializer
    queryset = Authors.objects.all().order_by('id')

    @swagger_auto_schema(
        operation_description="Get paginated list of authors",
        responses={200: AuthorsSerializer()}
    )
    @action(detail=False, methods=['get'])
    def list(self, request):
        page_number = request.GET.get('page', 1)
        size = request.GET.get('size', 10)
        
        try:
            page_number = int(page_number)
            size = int(size)
        except ValueError:
            return Response({"error": "Invalid page or size parameters"}, status=400)

        paginator = Paginator(self.get_queryset(), size)
        
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            return Response({
                "type": "authors",
                "authors": []
            }, status=200)
        except Exception:
            return Response({"error": "Unknown error"}, status=500)

        serializer = AuthorSerializer(
            page.object_list,
            many=True,
            context={'request': request}
        )

        return Response({
            "type": "authors",
            "authors": serializer.data
        })

    @swagger_auto_schema(
        operation_description="Get a single author by ID",
        responses={200: AuthorSerializer()}
        )
    
    @action(detail=True, methods=['get'])
    def retrieve(self, request, row_id):
        author = get_object_or_404(Authors, row_id = row_id)
        serializer = AuthorSerializer(author, context={'request': request})
        return Response(serializer.data)

    
    def get_queryset(self):
        return Authors.objects.all().order_by('id')
    
class IsOwnerOrPublic(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if obj.visibility == 'PUBLIC':
                return True
            if obj.visibility == 'FRIENDS' and request.user.is_authenticated:
                return request.user in obj.author.friends.all()
            return False
        return obj.author == request.user

class IsLocalAuthor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.local

# views.py
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrPublic]
    lookup_field = 'id'
    
    def get_queryset(self):
        author_serial = self.kwargs.get('author_serial')
        if author_serial:
            return Post.objects.filter(author__row_id=author_serial, is_deleted=False)
        return Post.objects.filter(is_deleted=False)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # POST /api/authors/{AUTHOR_SERIAL}/posts/
    def create(self, request, author_serial=None):
        author = get_object_or_404(Authors, row_id=author_serial)
        if not author.local:
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, author_serial=None):
        author = get_object_or_404(Authors, row_id=author_serial)
        queryset = self.filter_queryset(self.get_queryset())
        
        if not request.user.is_authenticated:
            queryset = queryset.filter(visibility='PUBLIC')
        elif request.user != author:
            if request.user in author.followers.all():
                queryset = queryset.filter(visibility__in=['PUBLIC', 'UNLISTED'])
            else:
                queryset = queryset.filter(visibility='PUBLIC')
        
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='posts/(?P<post_fqid>.+)')
    def get_by_fqid(self, request, post_fqid=None):
        post_id = post_fqid.split('/')[-1]
        post = get_object_or_404(Post, id=post_id)
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    def perform_create(self, serializer):
        if 'image' in self.request.data:
            image_data = self.request.data['image']
            fmt, imgstr = image_data.split(';base64,')
            ext = fmt.split('/')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=filename)
            serializer.save(image=data)
        else:
            serializer.save()


