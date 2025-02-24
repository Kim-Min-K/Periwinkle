from accounts.serializers import *
from accounts.models import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_yasg.utils import swagger_auto_schema
import uuid
from rest_framework.decorators import action
from django.core.paginator import Paginator

class FollowersSerializer(serializers.Serializer):
    type = serializers.CharField(default="followers")
    followers = authorSerializer(many=True)
    
class FollowRequestSerializerRaw(serializers.Serializer):
    type = serializers.CharField(default="follow")
    summary = serializers.CharField(default=None)
    actor = authorSerializer()
    object = authorSerializer()
    
class AuthorSerializer(serializers.Serializer):
    type = serializers.CharField(default="author")
    id = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    displayName = serializers.CharField(source="username")
    github = serializers.SerializerMethodField()
    profileImage = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()

    def get_id(self, obj):
        # return self.context['request'].build_absolute_uri(f'/api/authors/{obj.id}/')
        return obj.id

    def get_host(self, obj):
        # return self.context['request'].build_absolute_uri('/api/')
        return obj.host
    
    def get_github(self, obj):
        return f"https://github.com/{obj.github_username}"

    def get_profileImage(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return obj.avatar_url

    def get_page(self, obj):
        return self.context['request'].build_absolute_uri(f'/accounts/profile/{obj.username}')

class AuthorsSerializer(serializers.Serializer):
    type = serializers.CharField(default="authors")
    authors = AuthorSerializer(many=True)

class FollowersViewSet(GenericViewSet):
    serializer_class=FollowersSerializer

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        operation_description="Get the followers of an author",
        responses={200: serializer_class()}
    )
    def list(self, request, author_serial):
        try:
            author_uuid = uuid.UUID(hex=author_serial)  # Convert string to UUID
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

    def get_queryset(self):
        return Authors.objects.all().order_by('id')