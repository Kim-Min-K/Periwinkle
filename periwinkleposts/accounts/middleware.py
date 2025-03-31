from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve

class ApprovalRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_approved:
            # Define exempt paths
            exempt_paths = [
                reverse('accounts:approval_pending'),
                reverse('accounts:logout'),
                '/admin/',
                '/api/docs'
            ]
            
            # Check if current path is exempt
            if not any(request.path.startswith(path) for path in exempt_paths):
                return redirect('accounts:approval_pending')
                
        return self.get_response(request)

class DisableCSRF(MiddlewareMixin):
    """Middleware for disabling CSRF in a specified app name."""

    def process_request(self, request):
        """Preprocess the request."""
        app_name = "api"
        resolver_match = resolve(request.path_info)
        
        if resolver_match.app_name == app_name:
            setattr(request, '_dont_enforce_csrf_checks', True)