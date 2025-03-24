from rest_framework.permissions import IsAuthenticated
from .node_auth import NodeBasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response

class NodeAuthCheckView(APIView):
    authentication_classes = [NodeBasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Authentication successful!"})

