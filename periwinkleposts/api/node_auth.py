from django.conf import settings
from django.http import JsonResponse
import base64

def require_node_auth(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return JsonResponse({'error': 'Missing credentials'}, status=401)

        try:
            encoded = auth_header.split(' ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
        except Exception:
            return JsonResponse({'error': 'Invalid auth format'}, status=400)

        if username != settings.NODE_USERNAME or password != settings.NODE_PASSWORD:
            return JsonResponse({'error': 'Invalid credentials'}, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper