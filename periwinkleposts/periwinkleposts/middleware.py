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