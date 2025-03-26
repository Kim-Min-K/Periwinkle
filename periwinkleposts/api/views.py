from rest_framework.permissions import IsAuthenticated
from .node_auth import NodeBasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from utils.node_auth import require_node_auth
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_node_auth
def ping(request):
    return JsonResponse({'message': 'Auth OK'}, status=200)
    
class NodeAuthCheckView(APIView):
    authentication_classes = [NodeBasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Authentication successful!"})

