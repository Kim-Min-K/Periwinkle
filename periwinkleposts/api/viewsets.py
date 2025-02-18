from accounts.serializers import *
from accounts.models import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_yasg.utils import swagger_auto_schema
import uuid

class FollowersViewSet(GenericViewSet):
    serializer_class=FollowersSerializer

    @swagger_auto_schema(
        operation_description="Get the followers of an author",
        responses={200: serializer_class()}
    )
    def list(self, request, author_serial):
        try:
            author_uuid = uuid.UUID(hex=author_serial)  # Convert string to UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format'}, status=400)

        author = get_object_or_404(Authors, pk=author_uuid)

        serializer = self.get_serializer(instance=author)

        return Response(serializer.data)