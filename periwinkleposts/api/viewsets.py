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
from drf_yasg.inspectors import SwaggerAutoSchema

class FollowersSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        return ["Followers"]

class FollowersViewSet(GenericViewSet):
    swagger_schema=FollowersSchema
    serializer_class=authorsSerializer

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get the followers of an author",
        request_body=None,
        responses={200: serializer_class()}
    )
    def list(self, request, author_serial):
        try:
            author_uuid = author_serial  # Convert string to UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format'}, status=400)

        follower_ids = Follow.objects.filter(followee=author_uuid).values_list('follower_id', flat=True)  # Get all followers

        followers = Authors.objects.filter(row_id__in=follower_ids)
        serializer = self.serializer_class({"type":"followers", "authors": followers})

        return Response(serializer.data, 200)

class FolloweesSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        return ["Followees"]

class FolloweesViewSet(GenericViewSet):
    swagger_schema=FolloweesSchema
    serializer_class = UnfollowSerializer
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_description="Unfollow a followee of an author",
        request_body=None,
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
    
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get all followees of an author",
        request_body=None,
        responses={
            200: FolloweesSerializer(),
            400: "Invalid UUID format."
            }
    )
    def getFollowees(self, request, author_serial):
        try:
            author_uuid = author_serial  # Convert string to UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format'}, status=400)

        followees = Authors.objects.filter(row_id__in=Follow.objects.filter(follower=author_uuid).values_list('followee', flat=True))

        serializer = FolloweesSerializer({"followees":followees})

        return Response(serializer.data, status=200)


class FriendsSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        return ["Friends"]

class FriendsViewSet(GenericViewSet):
    swagger_schema=FriendsSchema
    serializer_class=authorsSerializer()
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get all friends of an author",
        request_body=None,
        responses={
            200: authorsSerializer(),
            404: "The author does not exists."
            }
    )
    def getFriends(self, request, author_serial):
        print(author_serial)
        author_uuid = author_serial

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
        serializer = authorsSerializer({"type": "friends", "authors":friends})

        return Response(serializer.data)

class FollowRequestSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        return ["Follow Requests"]

class FollowRequestViewSet(GenericViewSet):

    swagger_schema=FollowRequestSchema
    serializer_class=ActionSerializer

    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_description="Send a follow request to an author.",
        request_body=ActionSerializer,
        responses={
            201: ActionSerializer(),
            400: "Serializer errors. "
        }
    )
    def makeRequest(self, request, author_serial):
        try:
            with transaction.atomic():

                requestee = get_object_or_404(Authors, pk=author_serial)
                requester_json = request.data.get("actor")

                # Use requester object in database if it exists otherwise create it
                try:
                    requester = Authors.objects.get(id=requester_json["id"])
                except Authors.DoesNotExist:
                    requester_serializer = authorSerializer(data=requester_json)
                    if not requester_serializer.is_valid():
                        raise ValueError(requester_serializer.errors)
                    requester = requester_serializer.save()
                    
                serializer = ActionSerializer(action_type="follow", actor=requester, object=requestee)
                serializer.save()
                return Response(serializer.to_representation(), 200)

        except ValueError as e:
            # Return the validation error message
            return Response({"error": str(e)}, status=400)

        return Response({"message":"Follow request successfuly sent."}, status=200)
    
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get all follow requests of an author",
        request_body=None,
        responses={
            200: authorsSerializer(),
            404: "The author does not exists."
            }
    )
    def getFollowRequests(self, request, author_serial):
        author_uuid = author_serial

        author = get_object_or_404(Authors, pk=author_uuid)

        requesters_ids = FollowRequest.objects.filter(requestee=author).values_list('requester_id', flat=True)

        requesters = Authors.objects.filter(row_id__in=requesters_ids)

        # Serialize the friend objects
        serializer = authorsSerializer({"type":"incoming-follow-requests", "authors": requesters})
        
        return Response(serializer.data, status=200)
    
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get all outgoing follow requests of an author",
        request_body=None,
        responses={
            200: authorsSerializer(),
            400: "Invalid UUID format."
            }
    )
    def getOutGoingFollowRequests(self, request, author_serial):
        try:
            author_uuid = author_serial  # Convert string to UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format'}, status=400)

        author = Authors.objects.get(pk=author_uuid)

        requestee_ids = FollowRequest.objects.filter(requester=author).values_list('requestee_id', flat=True)

        requestees = Authors.objects.filter(row_id__in=requestee_ids)

        serializer = authorsSerializer({"type":"outgoing-follow-requests", "authors":requestees})

        return Response(serializer.data, status=200)
    
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_description="Accept the incoming follow request from the author with uuid 'request_serial' to the author with the uuid 'author_serial'. ",
        request_body=None,
        responses={
            200: ActionSerializer()
            }
    )
    def acceptFollowRequest(self, request, author_serial, requester_serial):
        try:
            with transaction.atomic():
                object = get_object_or_404(Authors, row_id=requester_serial)
                actor = get_object_or_404(Authors, row_id=author_serial)
                serializer = ActionSerializer(action_type="accept-follow-request", actor=actor, object=object)
                serializer.save()
                return Response(serializer.to_representation(), status=200)
        except ValueError as e:
            # Return the validation error message
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_description="Decline the incoming follow request from the author with uuid 'request_serial' to the author with the uuid 'author_serial'. ",
        request_body=None,
        responses={
            200: ActionSerializer()
            }
    )
    def declineFollowRequest(self, request, author_serial, requester_serial):
        try:
            with transaction.atomic():
                object = get_object_or_404(Authors, row_id=requester_serial)
                actor = get_object_or_404(Authors, row_id=author_serial)
                serializer = ActionSerializer(action_type="decline-follow-request", actor=actor, object=object)
                serializer.save()
                return Response(serializer.to_representation(), status=200)
        except ValueError as e:
            # Return the validation error message
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get 5 author suggests that the Author with uuid 'author_serial' can send a follow request.",
        request_body=None,
        responses={
            200: authorsSerializer()
            }
    )
    def getRequestSuggestions(self, request, author_serial):
        author_uuid = author_serial

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
        
        serializer = authorsSerializer({"type":"request-suggestions", "authors": suggestions})

        return Response(serializer.data, status=200)

    
class AuthorViewSet(GenericViewSet):
    serializer_class = AuthorSerializer
    queryset = Authors.objects.all().order_by('id')

    @swagger_auto_schema(
        operation_description="Get paginated list of authors",
        responses={200: AuthorSerializer()}
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
        print({"type": "authors", "authors": serializer.data})
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
        print(serializer.data)
        return Response(serializer.data)

    
    def get_queryset(self):
        return Authors.objects.all().order_by('id')
    

    @swagger_auto_schema(
        operation_description="Update an author's profile", 
        responses={200: AuthorSerializer()}
        )
    
    @action(detail=True, methods=['put'])
    def update(self, request, row_id=None):
        author = get_object_or_404(Authors, row_id=row_id)
        # get fields and update manually
        username = request.data.get('username', None)
        if username is not None:
            author.username = username

        display_name = request.data.get('displayName', None)
        if display_name is not None:
            author.displayName = display_name

        github = request.data.get('github', None)
        if github is not None:
            # if not github.startswith("https://github.com/"):
            #     github = "https://github.com/" + github
            
            # author.github_username = github
            author.github_username = github.replace("https://github.com/", "") #workaround for continous github.com concatenation


        email = request.data.get('email', None)
        if email is not None:
            author.email = email
            
        # avatar = request.data.get('avatar', None)
        # if avatar is not None:
        #     author.avatar = avatar
        profile_image = request.data.get('profileImage', None)
        if profile_image is not None:
            author.avatar_url = profile_image

        author.save()
        
        serializer = AuthorSerializer(author, context={'request': request})
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
        
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


