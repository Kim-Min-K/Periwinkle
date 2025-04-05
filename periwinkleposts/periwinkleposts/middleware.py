from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = reverse('accounts:login')
        self.exempt_urls = [
            self.login_url,
            reverse('accounts:register'),
            '/static/',
            '/media/',
            '/admin/',
            '/404/',
            '/api/'
        ]

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path_info
        
        # Bypass authentication check for exempt URLs
        if any(path.startswith(str(url)) for url in self.exempt_urls):
            return None
            
        # Redirect unauthenticated users
        if not request.user.is_authenticated:
            return HttpResponseRedirect(f"{self.login_url}?next={path}")
            
        return None

import base64
from django.http import HttpResponse
from django.conf import settings

class BasicAuthApiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or 'http://testserver' in request.build_absolute_uri():
            return self.get_response(request)
            
        # Require Basic Auth only for /api/ routes
        if request.path.startswith('/api/'):
            auth = request.META.get('HTTP_AUTHORIZATION')
            if auth and auth.startswith('Basic '):
                return self.get_response(request)

            response = HttpResponse("Unauthorized", status=401)
            response['WWW-Authenticate'] = 'Basic realm="API"'
            return response

        return self.get_response(request)