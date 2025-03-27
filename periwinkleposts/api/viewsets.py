from accounts.serializers import *
from accounts.models import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from drf_yasg import openapi
import uuid
import base64
from rest_framework.decorators import action
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import permissions
from django.urls import reverse
from api.serializers import *
from django.http import Http404
from drf_yasg.inspectors import SwaggerAutoSchema
from urllib.parse import unquote
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from .models import *
from django.db.models import Q
import requests
from urllib.parse import urlparse
import requests
from django.core.files.base import ContentFile

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

        author = get_object_or_404(Authors, row_id=author_serial)

        follower_ids = Follow.objects.filter(followee=author_uuid).values_list('follower_id', flat=True)  # Get all followers

        followers = Authors.objects.filter(row_id__in=follower_ids)

        active_followers = []
        for follower in followers:
            url = follower.host+"authors/"+str(author_serial)+"/followers/"+str(follower.id)
            response = requests.get(url)
            if response.status_code == 200:
                active_followers.append(follower)
            elif response.status_code == 404:
                Follow.objects.get(follower=follower, followee=author.row_id).delete()
            else:
                raise Exception(response.data)

        serializer = self.serializer_class({"type":"followers", "authors": active_followers})

        return Response(serializer.data, 200)

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Check if foreign_author_fqidD is a follower of author_serial",
        request_body=None,
        responses={
            200: "foreign_author_fqid is a follower of author_serial",
            404: "foreign_author_fqid is not an author/follower"
        }
    )
    def isFollower(self, request, author_serial, foreign_author_fqid):
        decoded_fqid = unquote(foreign_author_fqid)
        foreign_author = get_object_or_404(Authors, id=decoded_fqid)
        get_object_or_404(Follow, followee=author_serial, follower=foreign_author.row_id)
        return Response({"message": "foreign_author_fqid is a follower of author_serial"}, status=200)

        

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
        author_uuid = author_serial

        # Retrieve the author for whom we want to get friends
        author = get_object_or_404(Authors, pk=author_uuid)

        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        fake_request = factory.get(f"/authors/{author_serial}/followers/")  # Simulate a request

        # Get active followers (mutual followers)
        active_followers_fqid = {
            author["id"] for author in (FollowersViewSet.as_view({"get": "list"}))(fake_request, author_serial).data["authors"]
        }

        # Get all authors that this author follows (i.e., followees)
        following_ids = Follow.objects.filter(follower=author).values_list('followee_id', flat=True)

        following_fqids = set(Authors.objects.filter(row_id__in=following_ids).values_list('id', flat=True))

        # Find mutual friends
        friend_ids = list(following_fqids & active_followers_fqid)

        # Retrieve the friend Author objects
        friends = Authors.objects.filter(id__in=friend_ids)

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
                    requester_json["row_id"] = requester_json["id"].split("/")[-1]
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
        
        # Get up to 5 local authors
        suggestions = list(Authors.objects.exclude(row_id__in=followed_ids)
                                          .exclude(row_id=current_author.row_id)
                                          .exclude(row_id__in=request_ids)
                                          .exclude(is_staff=True)
                                          .order_by('?')[:5])

        if len(suggestions) < 5:
            nodes = ExternalNode.objects.all()
            for node in nodes:
                host = str(node.nodeURL) + "/api/"
                url = host+"authors/"
                response = requests.get(url)
                if response.status_code != 200:
                    continue
                external_authors = response.json()["authors"]
                print(external_authors)
                # Add external authors to suggestions
                for author_data in external_authors:
                    if len(suggestions) >= 5:
                        break
                    if not Authors.objects.filter(id=author_data["id"]).exists() and not Authors.objects.filter(github_username=author_data['github'].split("/")[-1]).exists():
                        
                        author_data['row_id'] = author_data['id'].split("/")[-1]
                        github_username = author_data['github'].split("/")[-1]
                        author_data['github_username'] = github_username

                        serializer = authorSerializer(data=author_data)
                        if not serializer.is_valid():
                            raise Exception("Error saving author suggestion because : " + str(serializer.errors))
                        author = serializer.save()
                        suggestions.append(author)
        
        serializer = authorsSerializer({"type":"request-suggestions", "authors": suggestions})

        return Response(serializer.data, status=200)

    
class AuthorViewSet(GenericViewSet):
    serializer_class = AuthorSerializer
    queryset = Authors.objects.filter(local=True, is_staff=0).order_by('id')

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

        print(request.build_absolute_uri("/api/"))
        paginator = Paginator(self.get_queryset().filter(host=request.build_absolute_uri("/api/")), size)
        
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

        serializer = AuthorObjectToJSONSerializer(
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
        return Authors.objects.exclude(is_staff=1).order_by('id')
    

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
    pagination_class = PageNumberPagination  # Add pagination class
    lookup_field = 'id'

    def get_queryset(self):
        author_serial = self.kwargs.get('author_serial')
        queryset = Post.objects.filter(is_deleted=False)
        
        if author_serial:
            queryset = queryset.filter(author__row_id=author_serial)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # POST /api/authors/{AUTHOR_SERIAL}/posts/
    def create(self, request, author_serial=None):
        # Ensure the author exists and is local
        author = get_object_or_404(Authors, row_id=author_serial)
        if not author.local:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, author)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer, author):
        # Extract media data from request
        image_data = self.request.data.get('image')
        video_data = self.request.data.get('video')
    
        save_kwargs = {'author': author}

        if image_data:
            if image_data.startswith(('http://', 'https://')):
                try:
                    response = requests.get(image_data, timeout=5)
                    response.raise_for_status()
                    filename = os.path.basename(urlparse(image_data).path)
                    unique_name = f"{uuid.uuid4()}_{filename}"
                    save_kwargs['image'] = ContentFile(response.content, name=unique_name)
                except Exception as e:
                    print(f"Error downloading image: {str(e)}")
            elif ';base64,' in image_data:
                fmt, imgstr = image_data.split(';base64,')
                ext = fmt.split('/')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                save_kwargs['image'] = ContentFile(base64.b64decode(imgstr), name=filename)
            else:
                save_kwargs['image'] = image_data
        serializer.save(**save_kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, author_serial=None):
        # Get base queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply visibility filters
        if not request.user.is_authenticated:
            queryset = queryset.filter(visibility='PUBLIC')
        elif author_serial and request.user.row_id != author_serial: 
            author = Authors.objects.get(row_id=author_serial)
            if request.user not in author.followers.all():
                queryset = queryset.filter(visibility='PUBLIC')

        # Use DRF's built-in pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='posts/(?P<post_fqid>.+)')
    def get_by_fqid(self, request, post_fqid=None):
        post_id = post_fqid.split('/')[-1]
        try:
            post = Post.objects.get(id=post_id, is_deleted=False)
        except Post.DoesNotExist:
            raise Http404("Post does not exist or has been deleted")
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    def perform_create(self, serializer):
        image_data = self.request.data.get('image')
        video_data = self.request.data.get('video')
        if image_data:
            if image_data.startswith(('http://', 'https://')):
                try:
                    response = requests.get(image_data, timeout=5)
                    response.raise_for_status()
                    filename = os.path.basename(urlparse(image_data).path)
                    unique_name = f"{uuid.uuid4()}_{filename}"
                    
                    serializer.save(
                        image=ContentFile(response.content, name=unique_name)
                    )
                except Exception as e:
                    # Handle download errors
                    print(f"Error downloading image: {str(e)}")
                    serializer.save()
            
            elif ';base64,' in image_data:
                fmt, imgstr = image_data.split(';base64,')
                ext = fmt.split('/')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                data = ContentFile(base64.b64decode(imgstr), name=filename)
                serializer.save(image=data)
            else:
                serializer.save(image=image_data)
        else:
            serializer.save()
            
    @swagger_auto_schema(
        operation_description="Get paginated list of all posts",
        responses={200: PostSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """Get all posts across all authors with pagination"""
        return self._paginated_posts_response(request)
            
    def _paginated_posts_response(self, request, author_serial=None):
            page_number = request.GET.get('page', 1)
            size = request.GET.get('size', 10)
            
            try:
                page_number = int(page_number)
                size = int(size)
            except ValueError:
                return Response({"error": "Invalid page or size parameters"}, status=400)

            # Base queryset
            queryset = Post.objects.filter(is_deleted=False)
            
            # Filter by author if specified
            if author_serial:
                queryset = queryset.filter(author__row_id=author_serial)

            # Apply visibility filters
            if not request.user.is_authenticated:
                queryset = queryset.filter(visibility='PUBLIC')
            elif not request.user.is_superuser:
                followee_ids = Follow.objects.filter(follower=request.user).values_list('followee_id', flat=True)
                queryset = queryset.filter(
                    Q(visibility='PUBLIC') |
                    # Q(visibility='UNLISTED', author__follower=request.user) |
                    # Q(visibility='UNLISTED', author__followee=request.user) |
                    Q(visibility='UNLISTED', author__row_id__in=followee_ids) |
                    Q(author=request.user)
                ).distinct()

            paginator = Paginator(queryset, size)
            
            try:
                page = paginator.page(page_number)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                return Response({
                    "type": "posts",
                    "posts": []
                }, status=200)

            serializer = PostSerializer(
                page.object_list,
                many=True,
                context={'request': request}
            )
            
            return Response({
                "type": "posts",
                "posts": serializer.data
            })


class NodeViewset(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    permission_classes = [IsAdminUser]
    queryset = ExternalNode.objects.all()
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            try:
                response = requests.get(
                    f'{validated_data["nodeURL"].rstrip("/")}/api/ping/',
                    auth=HTTPBasicAuth(validated_data["username"], validated_data["password"]),
                    timeout=5
                )
                if response.status_code != 200:
                    raise ValidationError("Invalid credentials")
            except requests.exceptions.ConnectionError:
                raise ValidationError("Node unreachable")

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    